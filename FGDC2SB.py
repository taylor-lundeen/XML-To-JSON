from Datetime_Utils import datetimeHandler
from Weblink_Utils import webLinkHandler
from Citation_Utils import citationHandler
from lxml import etree as etree
from email_validator import validate_email, EmailNotValidError
from io import BytesIO
import decimal
import re
import os
import json


class FGDC2SB:

    def __init__(self, input_file_name, input_xml_file):
        self.input_file = input_xml_file
        self.input_file_name = input_file_name

        #Lists of proper attribute orders for various data type
        self.citation_facet_order = ["citationType", "note", "edition", "parts"]
        self.contact_order = ["name", "type", "contactType", "organizationsPerson", "ttyPhone", "hours", "instructions",
                              "email", "jobTitle", "organization", "primaryLocation"]
        self.primary_location_order = ["officePhone", "faxPhone", "streetAddress", "mailAddress"]
        self.web_link_order = ["type", "uri", "rel", "title", "hidden"]

        """
        The self.xpath_* variables are used to define the path to navigate
        to in the xml file to retrieve a particular set of data
        """
        self.xpath_title = "idinfo/citation/citeinfo/title"
        self.xpath_abstract = "idinfo/descript/abstract"
        self.xpath_purpose = "idinfo/descript/purpose"
        self.xpath_supplemental = "idinfo/descript/supplinf"
        self.xpath_onlink = "idinfo/citation/citeinfo/onlink"
        self.xpath_browse_image = "//browse"
        self.xpath_network_resource = "//networkr"
        self.xpath_westbc = "idinfo/spdom/bounding/westbc"
        self.xpath_westbc_new = "idinfo/rseSpdom/bounding/westbc"
        self.xpath_eastbc = "idinfo/spdom/bounding/eastbc"
        self.xpath_eastbc_new = "idinfo/rseSpdom/bounding/eastbc"
        self.xpath_northbc = "idinfo/spdom/bounding/northbc"
        self.xpath_northbc_new = "idinfo/rseSpdom/bounding/northbc"
        self.xpath_southbc = "idinfo/spdom/bounding/southbc"
        self.xpath_southbc_new = "idinfo/rseSpdom/bounding/southbc"
        self.xpath_origin = "idinfo/citation/citeinfo/origin"
        self.xpath_themekey = "idinfo/keywords/theme"
        self.xpath_placekey = "idinfo/keywords/place"
        self.xpath_process_description = "dataqual/lineage/procstep/procdesc"
        self.xpath_process_contact = "dataqual/lineage/procstep/proccont/cntinfo"
        self.xpath_contact_point = "idinfo/ptcontac/cntinfo"
        self.xpath_contact_distribution = "distinfo/distrib/cntinfo"
        self.xpath_contact_metadata = "metainfo/metc/cntinfo"
        self.xpath_eainfo = "eainfo"
        self.xpath_pubdate = "idinfo/citation/citeinfo/pubdate"
        self.xpath_pubtime = "idinfo/citation/citeinfo/pubtime"
        self.xpath_timeperiod = "idinfo/timeperd/timeinfo"
        self.xpath_publish = "idinfo/citation/citeinfo/pubinfo/publish"
        self.xpath_publisher = "idinfo/citation/citeinfo/pubinfo/publisher"
        self.xpath_transfersize = "distinfo/stdorder/digform/digtinfo/transize"
        self.xpath_parentid = "idinfo/citation/citeinfo/lworkcit/citeinfo/onlink"
        self.xpath_citation_info = "idinfo/citation/citeinfo"
        self.xpath_main_update_freq = "idinfo/status/update"

        """
        The regex patterns used to search strings
        """

        self.mail_regex_pattern = re.compile('mail', re.IGNORECASE)
        self.gda_id_regex_pattern = re.compile('/.+?"gdaId"\s*:\s*"?(\d+)"?\s*.+/')
        self.basis_id_regex_pattern = re.compile('/\s*This project is (.+?) in the USGS BASIS\+ system.\s*/')

    def check_file_extension(self, file_name):
        """
        Check whether input file is of type xml
        :param file_name: name of input file
        :return: boolean for whether file extension is .xml or not
        """
        file_tup = os.path.splitext(file_name)
        is_xml_file = False
        if file_tup[1] == ".xml":
            is_xml_file = True

        return is_xml_file

    def get_xpath_text(self, xml_data, xml_path, single_item=False):
        """
        Finds text data within an xml file with a given xml path
        :param xml_data: The parsed xml file object
        :param xml_path: The path in the xml file to search for data in
        :param single_item: Boolean for whether to return a single text string or a list of text strings
        Should only be set to true if it is certain that there will only be one element for the xml path
        :return: A text string or a list of text strings for the input xml path
        """
        elements = xml_data.findall(xml_path)
        text_items = []
        for el in elements:
            text_items.append(el.text)
        if single_item == True:
            if len(text_items) > 0:
                text_items = text_items[0]
            else:
                text_items = ""

        return text_items

    def get_xpath_elements(self, xml_data, xml_path):
        """
        Finds xml objects within an xml file with a given xml path
        :param xml_data: The parsed xml file object
        :param xml_path: The path in the xml file to search for data in
        :return: An lxml etree element or elements representing the xml elements within that xml path
        """
        elements = xml_data.findall(xml_path)
        element_items = []
        for el in elements:
            element_items.append(el)

        return element_items

    def get_xpath_sub_elements(self, root_element, single_item=False, element_name=None):
        """
        Find xml elements within an xml element
        :param root_element: The xml element to search for elements within
        :param single_item: Boolean for whether to return a single element or a list of elements
        Should only be set to true if it is certain that there will only be one element returned
        :param element_name: Optional parameter to only search for elements with a specific name
        :return: An lxml etree element or list of lxml etree objects
        """
        sub_elements = []
        if element_name:
            for sub_element in root_element.iter(element_name):
                sub_elements.append(sub_element)
        else:
            for sub_element in root_element.iter():
                sub_elements.append(sub_element)
        if single_item == True:
            if len(sub_elements) > 0:
                sub_elements = sub_elements[0]
            else:
                sub_elements = None

        return sub_elements

    def get_xpath_parent_elements(self, root_element, num_iterations, iteration_num=0):
        """
        Gets the parent element for an xml element
        :param root_element: The xml element to get the parent element for
        :param num_iterations: The number of levels up the xml hierarchy to get the parent xml element for
        :param iteration_num: The number of iteration of this recursive function which have already been executed
        Example: a parent element of a parent elements would be 2 levels up the xml hierarchy
        :return: The parent xml element
        """
        i = iteration_num
        parent_elm = root_element.getparent()
        i += 1
        while i < num_iterations:
            return self.get_xpath_parent_elements(parent_elm, num_iterations, iteration_num=i)

        return parent_elm

    def reorder_dict_keys(self, dict, key_order_list):
        """
        Reorders the dictionary by key value
        :param dict: The input dictionary
        :param key_order_list: The list of keys in the order they should be in
        :return: A reordered dictionary
        """
        old_dict_keys = dict.keys()
        new_dict = {}
        for key in key_order_list:
            if key in old_dict_keys:
                new_dict[key] = dict[key]

        return new_dict

    def get_description(self, xml_data):
        """
        Generates the description and summary of the data in the xml
        :param xml_data: The parsed xml file object
        :return: A full description and a truncated summary of the xml document
        """
        summary = ""
        description = self.get_xpath_text(xml_data, self.xpath_abstract, single_item=True)
        if description:
            desc_len = len(description)
            summary = description
            if desc_len > 745:
                for i in reversed(range(0, 745)):
                    if description[i] == " ":
                        desc_section = description[:(i+1)]
                        summary = desc_section + "[...]"
                        break

        return description, summary

    def get_identifiers(self, xml_data):
        """
        Gets the GDA ID and Basis ID values from the xml
        :param xml_data: The parsed xml file object
        :return: GDA ID and Basis ID values
        """
        identifiers = []
        supplemental_el = self.get_xpath_text(xml_data, self.xpath_supplemental, single_item=True)
        if supplemental_el:
            # Extract GDA ID using regex
            gda_matcher = self.gda_id_regex_pattern.search(supplemental_el)
            if gda_matcher:
                gda_id = gda_matcher[0]
                identifier = {
                    "scheme": "gda",
                    "type": "id",
                    "key": gda_id
                }
                identifiers.append(identifier)

            # Extract Basis ID using regex
            basis_matcher = self.basis_id_regex_pattern.search(supplemental_el)
            if basis_matcher:
                basis_id = basis_matcher[0]
                identifier = {
                    "scheme": "BASIS+",
                    "type": "",
                    "key": basis_id
                }
                identifiers.append(identifier)

        return identifiers

    def create_bounding_box(self, xml_data):
        """
        Generate a bounding box from the geographic coordinate data
        :param xml_data: The parsed xml file object
        :return: A dictionary with the geographic coordinates for the bounding box
        """
        west_bc = self.get_xpath_text(xml_data, self.xpath_westbc, single_item=True)
        if not west_bc:
            west_bc = self.get_xpath_text(xml_data, self.xpath_westbc_new, single_item=True)

        east_bc = self.get_xpath_text(xml_data, self.xpath_eastbc, single_item=True)
        if not east_bc:
            east_bc = self.get_xpath_text(xml_data, self.xpath_eastbc_new, single_item=True)

        north_bc = self.get_xpath_text(xml_data, self.xpath_northbc, single_item=True)
        if not north_bc:
            north_bc = self.get_xpath_text(xml_data, self.xpath_northbc_new, single_item=True)

        south_bc = self.get_xpath_text(xml_data, self.xpath_southbc, single_item=True)
        if not south_bc:
            south_bc = self.get_xpath_text(xml_data, self.xpath_southbc_new, single_item=True)

        spatial_dict = {}
        min_x = None
        min_y = None
        max_x = None
        max_y = None

        if west_bc and east_bc and north_bc and south_bc:
            if float(east_bc) > float(west_bc):
                max_x = float(east_bc)
                min_x = float(west_bc)
            else:
                max_x = float(west_bc)
                min_x = float(east_bc)

            if float(north_bc) > float(south_bc):
                max_y = float(north_bc)
                min_y = float(south_bc)
            else:
                max_y = float(south_bc)
                min_y = float(north_bc)

        if min_x is not None and max_x is not None and min_y is not None and max_y is not None:
            spatial_dict = {"boundingBox": {"minX": min_x,
                                            "maxX": max_x,
                                            "minY": min_y,
                                            "maxY": max_y}}

        return spatial_dict

    def handle_single_datetime(self, element):
        """
        Get a string object with the date and/or time from elements
        which has just a single date or time
        :param element: An xml element with datetime information
        :return: A string with the datetime information
        """
        caldate = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="caldate")
        time = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="time")
        full_datetime_string = ""
        if caldate is not None:
            str = caldate.text
            caldate_tester = datetimeHandler(str)
            valid_date, date_format = caldate_tester.test_date_string()
            if valid_date == True:
                date_handler = datetimeHandler(str)
                formatted_date_string = date_handler.convert_date_format(date_format)
                full_datetime_string += formatted_date_string
        if time is not None:
            str = time.text
            time_tester = datetimeHandler(str)
            valid_time, time_format = time_tester.test_time_string()
            if valid_time == True:
                time_handler = datetimeHandler(str)
                formatted_time_string = time_handler.convert_time_format(time_format)
                full_datetime_string += formatted_time_string

        return full_datetime_string

    def handle_multi_datetime(self, element, label="Info Date (multi)"):
        """
        Get a string object with the date and/or time from elements
        which have more than one object with a date or time
        :param element: An XML element with datetime information
        :return: A dictionary with the datetime information
        """
        sngdates = self.get_xpath_sub_elements(root_element=element, single_item=False, element_name="sngdate")
        multi_dates = []
        if len(sngdates) > 0:
            for sngdate_elm in sngdates:
                handled_date = self.handle_single_datetime(sngdate_elm)
                if handled_date:
                    date_dict = {
                        "type": "Info",
                        "dateString": handled_date,
                        "label": label
                    }
                    multi_dates.append(date_dict)

        return multi_dates

    def handle_range_datetime(self, element):
        """
        Get a string object with the date and/or time from elements which have
        date and/or time values that include a duration of time rather than a
        single point in time
        :param element: An XML element with the datetime information
        :return: A list of dictionaries with start and end datetime information
        """
        range_dates = []
        begin_datetime_string = ""
        end_datetime_string = ""
        begdate = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="begdate")
        begtime = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="begtime")
        enddate = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="enddate")
        endtime = self.get_xpath_sub_elements(root_element=element, single_item=True, element_name="endtime")

        if begdate is not None:
            str = begdate.text
            begdate_tester = datetimeHandler(str)
            valid_date, date_format = begdate_tester.test_date_string()
            if valid_date == True:
                date_handler = datetimeHandler(str)
                formatted_date_string = date_handler.convert_date_format(date_format)
                begin_datetime_string += formatted_date_string

        if begtime is not None:
            str = begtime.text
            begtime_tester = datetimeHandler(str)
            valid_time, time_format = begtime_tester.test_time_string()
            if valid_time == True:
                time_handler = datetimeHandler(str)
                formatted_time_string = time_handler.convert_time_format(time_format)
                begin_datetime_string += formatted_time_string

        if enddate is not None:
            str = enddate.text
            enddate_tester = datetimeHandler(str)
            valid_date, date_format = enddate_tester.test_date_string()
            if valid_date == True:
                date_handler = datetimeHandler(str)
                formatted_date_string = date_handler.convert_date_format(date_format)
                end_datetime_string += formatted_date_string

        if endtime:
            str = endtime.text
            endtime_tester = datetimeHandler(str)
            valid_time, time_format = endtime_tester.test_time_string()
            if valid_time == True:
                time_handler = datetimeHandler(str)
                formatted_time_string = time_handler.convert_time_format(time_format)
                end_datetime_string += formatted_time_string

        if begin_datetime_string:
            date_dict = {
                "type": "Start",
                "dateString": begin_datetime_string,
                "label": ""
            }
            range_dates.append(date_dict)

        if end_datetime_string:
            date_dict = {
                "type": "End",
                "dateString": end_datetime_string,
                "label": ""
            }
            range_dates.append(date_dict)

        return range_dates

    def get_publication_date_info(self, xml_data):
        """
        Get attribute info for publication date and time
        Publication dates can be "Unknown", "Unpublished Material", or a "free date"
        see http://www.fgdc.gov/standards/projects/FGDC-standards-projects/metadata/base-metadata/v2_0698.pdf page 53
        :param xml_data: The parsed xml file object
        :return: A list of dictionaries with date and time info for a given publication
        """
        pubdate = self.get_xpath_text(xml_data, self.xpath_pubdate, single_item=True)
        pubtime = self.get_xpath_text(xml_data, self.xpath_pubtime, single_item=True)
        dates = []

        if pubdate and pubdate != "Unpublished Material" and pubdate != "Unknown":
            date_string = ""
            pubdate_tester = datetimeHandler(pubdate)
            valid_date, date_format = pubdate_tester.test_date_string()
            if valid_date == True:
                date_handler = datetimeHandler(pubdate)
                formatted_date_string = date_handler.convert_date_format(date_format)
                date_string += formatted_date_string
            if pubtime and pubtime != "Unknown":
                pubtime_tester = datetimeHandler(pubtime)
                valid_time, time_format = pubtime_tester.test_time_string()
                if valid_time == True:
                    time_handler = datetimeHandler(pubtime)
                    formatted_time_string = time_handler.convert_time_format(time_format)
                    date_string += formatted_time_string

            if date_string:
                date_dict = {
                    "type": "Publication",
                    "dateString": date_string,
                    "label": "Publication Date"
                }
                dates.append(date_dict)

        return dates

    def get_time_period_info(self, xml_data):
        """
        Get info for Time Period related to the xml document: http://www.fgdc.gov/metadata/csdgm/09.html
        :param xml_data: The parsed xml file object
        :return: A list which includes sets of time period info
        """
        time_perd = self.get_xpath_elements(xml_data, self.xpath_timeperiod)
        time_periods = []
        if len(time_perd) > 0:
            for time_perd_elm in time_perd:
                sngdates = self.get_xpath_sub_elements(root_element=time_perd_elm, single_item=False, element_name="sngdate")
                mdattims = self.get_xpath_sub_elements(root_element=time_perd_elm, single_item=False, element_name="mdattim")
                rngdates = self.get_xpath_sub_elements(root_element=time_perd_elm, single_item=False, element_name="rngdates")
                if len(sngdates) > 0:
                    for sngdate_elm in sngdates:
                        parent_elm = self.get_xpath_parent_elements(sngdate_elm, 1)
                        if parent_elm.tag != "mdattim":
                            single_date = self.handle_single_datetime(sngdate_elm)
                            if single_date:
                                date_dict = {
                                    "type": "Info",
                                    "dateString": single_date,
                                    "label": "Time Period"
                                }
                                time_periods.append(date_dict)
                if len(mdattims) > 0:
                    for mdattim_elm in mdattims:
                        multi_dates = self.handle_multi_datetime(mdattim_elm, "Time Period")
                        if len(multi_dates) > 0:
                            for md in multi_dates:
                                time_periods.append(md)
                if len(rngdates) > 0:
                    for rngdates_elm in rngdates:
                        range_dates = self.handle_range_datetime(rngdates_elm)
                        if len(range_dates) > 0:
                            for rd in range_dates:
                                time_periods.append(rd)

        return time_periods

    def get_citation_info(self, citation_element):
        """
        Gets citation information for series, publisher, place, and larger work citations
        :param citation_element: An xml element with citation information
        :return: A list of sets of citation metadata
        """
        citation_part = []
        if citation_element.tag == "serinfo":
            for sub_element in citation_element:
                serinfo_handler = citationHandler(element=sub_element)
                series_name_value, series_issue_value = serinfo_handler.get_publication_series_info()
                if len(series_name_value) > 0:
                    citation_part.append(series_name_value)
                if len(series_issue_value) > 0:
                    citation_part.append(series_issue_value)
        if citation_element.tag == "pubinfo":
            pubinfo_handler = citationHandler(element=citation_element)
            publisher_and_place_info = pubinfo_handler.get_publisher_and_place()
            if len(publisher_and_place_info) > 0:
                for ppi in publisher_and_place_info:
                    citation_part.append(ppi)
        if citation_element.tag == "lworkcit":
            lworkcit_handler = citationHandler(element=citation_element)
            for sub_element in citation_element:
                larger_work_citations = []
                if sub_element.tag == "citeinfo":
                    larger_work_citations = lworkcit_handler.get_larger_work_citation()
                    for sub_sub_element in sub_element:
                        if sub_sub_element.tag == "onlink":
                            onlink_handler = citationHandler(element=sub_sub_element)
                            sb2_citation_part = onlink_handler.get_type_and_value("2nd Online Linkage")
                            if len(sb2_citation_part) > 0:
                                citation_part.append(sb2_citation_part)
                if len(larger_work_citations) > 0:
                    for lwc in larger_work_citations:
                        citation_part.append(lwc)

        return citation_part

    def create_citation_facets(self, xml_data):
        """
        Create citation facets - multiple and with citation parts
        For FGDC citation mapping documentation see:  http://www.fgdc.gov/metadata/csdgm/08.html
        :param xml_data: The parsed xml file object
        :return: A list of sets of citation metadata
        """
        citation_list = self.get_xpath_elements(xml_data, self.xpath_citation_info)
        sb2_facet_list = []
        if len(citation_list) > 0:
            sb2_citation_facet_list = []
            for citation_elm in citation_list:
                sb2_citation_facet = {}
                sb2_citation_part_list = []
                for sub_element in citation_elm:
                    if sub_element.tag == "origin":
                        origin_handler = citationHandler(element=sub_element)
                        sb2_citation_part = origin_handler.get_type_and_value("Originator")
                        if len(sb2_citation_part) > 0:
                            sb2_citation_part_list.append(sb2_citation_part)
                    if sub_element.tag == "pubdate":
                        pubdate_handler = citationHandler(element=sub_element)
                        sb2_citation_part = pubdate_handler.get_type_and_value("Publication Date")
                        if len(sb2_citation_part) > 0:
                            sb2_citation_part_list.append(sb2_citation_part)
                    if sub_element.tag == "pubtime":
                        pubtime_handler = citationHandler(element=sub_element)
                        sb2_citation_part = pubtime_handler.get_type_and_value("Publication Time")
                        if len(sb2_citation_part) > 0:
                            sb2_citation_part_list.append(sb2_citation_part)
                    if sub_element.tag == "title":
                        title_handler = citationHandler(element=sub_element)
                        sb2_citation_part = title_handler.get_type_and_value("Title")
                        if len(sb2_citation_part) > 0:
                            sb2_citation_part_list.append(sb2_citation_part)
                    if sub_element.tag == "edition":
                        edition = sub_element.text
                        if edition:
                            sb2_citation_facet["edition"] = edition
                    if sub_element.tag == "geoform":
                        geo_form = sub_element.text
                        if geo_form:
                            sb2_citation_facet["citationType"] = geo_form
                    if sub_element.tag == "othercit":
                        other_citation = sub_element.text
                        sb2_citation_facet["note"] = other_citation
                    if sub_element.tag == "onlink":
                        onlink_handler = citationHandler(element=sub_element)
                        sb2_citation_part = onlink_handler.get_type_and_value("Online Linkage")
                        if len(sb2_citation_part) > 0:
                            sb2_citation_part_list.append(sb2_citation_part)
                    citation_part = self.get_citation_info(sub_element)
                    if len(citation_part) > 0:
                        for cp in citation_part:
                            sb2_citation_part_list.append(cp)
                # Add part list to facet
                if sb2_citation_part_list:
                    sb2_citation_facet["parts"] = sb2_citation_part_list
                # Add facet to facet list
                if sb2_citation_facet:
                    ordered_sb2_citation_facet = self.reorder_dict_keys(sb2_citation_facet, self.citation_facet_order)
                    sb2_citation_facet_list.append(ordered_sb2_citation_facet)
            # Set citation facet list to all facets list
            if sb2_citation_facet_list:
                for facet in sb2_citation_facet_list:
                    sb2_facet_list.append(facet)

        return sb2_facet_list

    def generate_address_info(self, address_element):
        """
        Get attribute info for an address
        :param address_element: An xml element with address info
        :return: A dictionary with address info and a string representing the address type
        """
        address_dict = {}
        address_type = "streetAddress"
        addrtype = self.get_xpath_sub_elements(root_element=address_element, single_item=True, element_name="addrtype")
        if addrtype is not None and self.mail_regex_pattern.search(addrtype.text):
            address_type = "mailAddress"
        address_line_text = []
        address_lines = self.get_xpath_sub_elements(root_element=address_element, single_item=False, element_name="address")
        if len(address_lines) > 0:
            for address_line in address_lines:
                address_line_text.append(address_line.text)
            if len(address_line_text) == 2:
                address_dict["line1"] = address_line_text[0]
                address_dict["line2"] = address_line_text[1]
            else:
                address_dict["line1"] = "\n".join(address_line_text)
        city = self.get_xpath_sub_elements(root_element=address_element, single_item=True, element_name="city")
        if city is not None:
            address_dict["city"] = city.text
        state = self.get_xpath_sub_elements(root_element=address_element, single_item=True, element_name="state")
        if state is not None:
            address_dict["state"] = state.text
        postal = self.get_xpath_sub_elements(root_element=address_element, single_item=True, element_name="postal")
        if postal is not None:
            address_dict["zip"] = postal.text
        country = self.get_xpath_sub_elements(root_element=address_element, single_item=True, element_name="country")
        if country is not None:
            address_dict["country"] = country.text

        return address_dict, address_type

    def generate_primary_location_info(self, location_element):
        """
        Create a dictionary with attribute info for a primary location
        :param location_element: The xml element with info about the primary location
        :return: a dictionary with info about the primary location
        """
        primary_location_dict = {}
        cntaddr = self.get_xpath_sub_elements(root_element=location_element, single_item=True, element_name="cntaddr")
        if cntaddr is not None:
            address_dict, address_type = self.generate_address_info(cntaddr)
            if len(address_dict) > 0:
                primary_location_dict[address_type] = address_dict
        cntvoice = self.get_xpath_sub_elements(root_element=location_element, single_item=True, element_name="cntvoice")
        if cntvoice is not None:
            primary_location_dict["officePhone"] = cntvoice.text
        cntfax = self.get_xpath_sub_elements(root_element=location_element, single_item=True, element_name="cntfax")
        if cntfax is not None:
            primary_location_dict["faxPhone"] = cntfax.text
        ordered_primary_location_dict = self.reorder_dict_keys(primary_location_dict, self.primary_location_order)

        return ordered_primary_location_dict

    def load_party(self, contact_type, cntinfo=None):
        """
        Get the metadata for a contact
        :param contact_type: The type of contact
        :param cntinfo: The xml element with info about a contact
        :return: A dictionary with the metadata for a contact
        """
        contact = {}
        contact["type"] = contact_type
        if cntinfo is not None:
            cntperp = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cntperp")
            if cntperp is not None:
                contact["contactType"] = "person"
                cntper = self.get_xpath_sub_elements(root_element=cntperp, single_item=True, element_name="cntper")
                if cntper is not None:
                    contact["name"] = cntper.text
                cntorg = self.get_xpath_sub_elements(root_element=cntperp, single_item=True, element_name="cntorg")
                if cntorg is not None:
                    organization = {}
                    organization["displayText"] = cntorg.text
                    contact["organization"] = organization
            else:
                cntorgp = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cntorgp")
                if cntorgp is not None:
                    contact["contactType"] = "organization"
                    cntorg = self.get_xpath_sub_elements(root_element=cntorgp, single_item=True, element_name= "cntorg")
                    cntper = self.get_xpath_sub_elements(root_element=cntorgp, single_item=True, element_name= "cntper")
                    if cntorg is not None:
                        contact["name"] = cntorg.text
                    if cntper is not None:
                        contact["organizationsPerson"] = cntper.text
            cntpos = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cntpos")
            if cntpos is not None:
                contact["jobTitle"] = cntpos.text
            primary_location_dict = self.generate_primary_location_info(cntinfo)
            if len(primary_location_dict) > 0:
                contact["primaryLocation"] = primary_location_dict
            email = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cntemail")
            if email is not None:
                #Verify that email address value is a valid email address
                is_valid = True
                try:
                    validate_email(email.text).email
                except EmailNotValidError:
                    is_valid = False
                if is_valid == True:
                    contact["email"] = email.text
            cnttdd = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cnttdd")
            if cnttdd is not None:
                contact["ttyPhone"] = cnttdd.text
            hours = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="hours")
            if hours is not None:
                contact["hours"] = hours.text
            cntinst = self.get_xpath_sub_elements(root_element=cntinfo, single_item=True, element_name="cntinst")
            if cntinst is not None:
                contact["instructions"] = cntinst.text
        ordered_contact = self.reorder_dict_keys(contact, self.contact_order)

        return ordered_contact

    def load_parties(self, xml_data, contact_xpaths=None):
        """
        Get metadata for each of the contacts
        :param xml_data: The parsed xml file object
        :param contact_xpaths: A dictionary with contact types and corresponding xml paths
        :return: A list of dictionaries with the data for each contact
        """
        parties = []

        if contact_xpaths is None:
            contact_xpaths = {
                "Point of Contact": self.xpath_contact_point,
                "Process Contact": self.xpath_process_contact,
                "Metadata Contact": self.xpath_contact_metadata,
                "Distributor": self.xpath_contact_distribution
            }

        for xpath in contact_xpaths.keys():
            contacts = self.get_xpath_elements(xml_data, contact_xpaths[xpath])
            if len(contacts) > 0:
                for contact in contacts:
                    party = self.load_party(xpath, contact)
                    if party:
                        parties.append(party)
                        if party["contactType"] == "organization" and "organizationsPerson" in party:
                            orgPerson = {}
                            organization = {}
                            orgPerson["contactType"] = "person"
                            orgPerson["type"] = party["type"]
                            orgPerson["name"] = party["organizationsPerson"]
                            orgPerson["organization"] = organization
                            if "name" in party:
                                organization["displayText"] = party["name"]
                            if "primaryLocation" in party:
                                orgPerson["primaryLocation"] = party["primaryLocation"]
                            if "email" in party:
                                orgPerson["email"] = party["email"]
                            if "jobTitle" in party:
                                orgPerson["jobTitle"] = party["jobTitle"]
                            ordered_orgPerson = self.reorder_dict_keys(orgPerson, self.contact_order)
                            parties.append(ordered_orgPerson)
                        if party["contactType"] == "person" and "organization" in party:
                            personsOrg = {}
                            personsOrg["contactType"] = "organization"
                            personsOrg["type"] = party["type"]
                            if "organization" in party:
                                personsOrg["name"] = (party["organization"])["displayText"]
                            if "primaryLocation" in party:
                                personsOrg["primaryLocation"] = party["primaryLocation"]
                            if "email" in party:
                                personsOrg["email"] = party["email"]
                            if "jobTitle" in party:
                                personsOrg["jobTitle"] = party["jobTitle"]
                            ordered_personsOrg = self.reorder_dict_keys(personsOrg, self.contact_order)
                            parties.append(ordered_personsOrg)

        return parties

    def create_contact(self, xml_data, xml_path, contact_type):
        """
        Get name and type of a contact
        :param xml_data: The parsed xml file object
        :param xml_path: The xml path to get info about contacts from
        :param contact_type: The type of contact
        :return: A dictionary with name and type of a contact
        """
        contact_info = []
        text_items = self.get_xpath_text(xml_data, xml_path)
        if text_items:
            for item in text_items:
                contact_dict = {
                    "name": item,
                    "type": contact_type
                }
                contact_info.append(contact_dict)

        return contact_info

    def generate_contact_info(self, xml_data):
        """
        Get info for all types of contacts
        :param xml_data: The parsed xml file object
        :return: A list of dictonaries with metadata for each contact
        """
        # Get contact data
        contact_xpaths = {
            "Point of Contact": self.xpath_contact_point,
            "Process Contact": self.xpath_process_contact
        }

        contact_list = []
        loaded_contacts = self.load_parties(xml_data, contact_xpaths)
        if len(loaded_contacts) > 0:
            for lc in loaded_contacts:
                contact_list.append(lc)

        # Data owner
        origin_list = self.create_contact(xml_data, self.xpath_origin, "Originator")
        if len(origin_list) > 0:
            for origin_item in origin_list:
                contact_list.append(origin_item)

        contact_xpaths = {
            "Metadata Contact": self.xpath_contact_metadata
        }

        loaded_contacts = self.load_parties(xml_data, contact_xpaths)
        if len(loaded_contacts) > 0:
            for lc in loaded_contacts:
                contact_list.append(lc)

        # Publisher
        publisher_list = self.create_contact(xml_data, self.xpath_publisher, "Publisher")
        if len(publisher_list) > 0:
            for publisher_item in publisher_list:
                contact_list.append(publisher_item)

        """
        Alternate Mapping for Publisher see:  http://www.fgdc.gov/metadata/csdgm/08.html
        Mapping verified against existing FGDC XML files
        """
        publish_list = self.create_contact(xml_data, self.xpath_publish, "Publisher")
        if len(publish_list) > 0:
            for publish_item in publish_list:
                contact_list.append(publish_item)

        contact_xpaths = {
            "Distributor": self.xpath_contact_distribution
        }

        loaded_contacts = self.load_parties(xml_data, contact_xpaths)
        if len(loaded_contacts) > 0:
            for lc in loaded_contacts:
                contact_list.append(lc)

        return contact_list

    def get_network_resource_info(self, xml_data, network_res_elm):
        """
        Gets the network resource web link data
        :param xml_data: The parsed xml file object
        :param network_res_elm: The xml element with the network resource data
        :return: A dictionary with the network resource data
        """
        network_link_handler = webLinkHandler(network_res_elm.text)
        network_link = network_link_handler.create_web_link()
        if len(network_link) > 0:
            digform_elm = self.get_xpath_parent_elements(network_res_elm, 5)
            digform_list = self.get_xpath_sub_elements(root_element=digform_elm, single_item=False, element_name="formname")
            try:
                digform_transize_str = self.get_xpath_text(xml_data, self.xpath_transfersize, single_item=True)
                digform_transize = decimal.Decimal(digform_transize_str)
                transfer_size = int(digform_transize * 1048576)
            except:
                transfer_size = 0

            for dl in digform_list:
                text = dl.text
                network_link["title"] = text
                if transfer_size != 0:
                    network_link["length"] = transfer_size

        return network_link

    def generate_web_links(self, xml_data, links, source_url=None):
        """
        Get web link data
        :param xml_data: The parsed xml file object
        :param links: A list of data for web links
        :param source_url: Optional parameter with the URL for original source
        :return: A list of dictionaries with metadata for each web link
        """
        web_links = []

        # Self link
        if source_url:
            self_link = {
                "type": "Original Source",
                "uri": source_url,
                "rel": "self",
                "title": "Original Source Metadata"
            }
            web_links.append(self_link)

        if len(links) > 0:
            for link_elm in links:
                link_handler = webLinkHandler(link_elm)
                link = link_handler.create_web_link()
                link["type"] = "Online Link"
                link["uri"] = link_elm
                ordered_link = self.reorder_dict_keys(link, self.web_link_order)
                web_links.append(ordered_link)

        online_links = self.get_xpath_text(xml_data, self.xpath_onlink)
        if len(online_links) > 0:
            for online_link_elm in online_links:
                online_link_handler = webLinkHandler(online_link_elm)
                online_link = online_link_handler.create_web_link()
                if len(online_link) > 0:
                    online_link["type"] = "Online Link"
                    online_link["uri"] = online_link_elm
                    ordered_online_link = self.reorder_dict_keys(online_link, self.web_link_order)
                    web_links.append(ordered_online_link)

        browse_image_list = self.get_xpath_elements(xml_data, self.xpath_browse_image)
        if len(browse_image_list) > 0:
            for browse_elm in browse_image_list:
                browsen_elm = self.get_xpath_sub_elements(root_element=browse_elm, single_item=True, element_name="browsen")
                browsed_elm = self.get_xpath_sub_elements(root_element=browse_elm, single_item=True, element_name="browsed")
                browse_link = {}
                if browsen_elm is not None:
                    browse_link_handler = webLinkHandler(browsen_elm.text)
                    browse_link = browse_link_handler.create_web_link()
                if browsed_elm is not None and len(browse_link) > 0:
                    browse_link["title"] = browsed_elm.text
                if len(browse_link) > 0:
                    browse_link["type"] = "browseImage"
                    ordered_browse_link = self.reorder_dict_keys(browse_link, self.web_link_order)
                    web_links.append(ordered_browse_link)

        network_link_list = self.get_xpath_elements(xml_data, self.xpath_network_resource)
        for network_resource_elm in network_link_list:
            network_link = self.get_network_resource_info(xml_data, network_resource_elm)
            if len(network_link) > 0:
                ordered_network_link = self.reorder_dict_keys(network_link, self.web_link_order)
                web_links.append(ordered_network_link)

        return web_links

    def get_tag_info(self, tag_element, kt_text):
        """
        Gets the time and place info for a tag to itentify the type of data in the xml file
        link: http://www.fgdc.gov/metadata/csdgm/01.html - See 1.6
        :param tag_element: An xml element for a tag
        :param kt_text: The text of a themeky or placekt xml element
        :return: A dictionary representing a tag
        """
        this_tag = tag_element.text
        sb_tag = {}
        if this_tag and len(this_tag) <= 80:
            sb_tag["type"] = "Theme"
            if kt_text:
                sb_tag["scheme"] = kt_text
            sb_tag["name"] = this_tag

        return sb_tag

    def create_tags(self, xml_data):
        """
        Get data for a tag to itentify the type of data in the xml file
        link: http://www.fgdc.gov/metadata/csdgm/01.html - See 1.6
        :param xml_data: The parsed xml file object
        :return: A list of dictionaries with metadata for each tag
        """
        tag_list = []
        theme_list = self.get_xpath_elements(xml_data, self.xpath_themekey)
        for theme_elm in theme_list:
            themekt = ""
            themekt_el = self.get_xpath_sub_elements(root_element=theme_elm, single_item=True, element_name="themekt")
            themekey_elms = self.get_xpath_sub_elements(root_element=theme_elm, single_item=False, element_name="themekey")
            if themekt_el is not None:
                themekt = themekt_el.text
            for te in themekey_elms:
                sb_tag = self.get_tag_info(te, themekt)
                if len(sb_tag) > 0:
                    tag_list.append(sb_tag)

        place_list = self.get_xpath_elements(xml_data, self.xpath_placekey)
        for place_elm in place_list:
            placekt = ""
            placekt_el = self.get_xpath_sub_elements(root_element=place_elm, single_item=True, element_name="placekt")
            placekey_elms = self.get_xpath_sub_elements(root_element=place_elm, single_item=False, element_name="placekey")
            if placekt_el is not None:
                placekt = placekt_el.text
            for pe in placekey_elms:
                sb_tag = self.get_tag_info(pe, placekt)
                if len(sb_tag) > 0:
                    tag_list.append(sb_tag)

        return tag_list

    def create_item(self, parent_id=None, source_url=None):
        """
        Generates a json object for the input xml data in sbjson form and exports it
        :param parent_id: Optional parameter with the parent id for the sciencebase item to be created
        :param source_url: Optional parameter with the URL for original source
        """
        # Check if file is xml
        is_xml_file = self.check_file_extension(self.input_file_name)
        if is_xml_file == False:
            raise Exception("Input file is not an xml file")

        # Parse the xml file
        xml_bytes = BytesIO(self.input_file)
        xml_data = etree.parse(xml_bytes)

        # Get parent id from crossref container
        parent_id_els = self.get_xpath_text(xml_data, self.xpath_parentid)
        non_parent_online_links = []

        if parent_id is None:
            if len(parent_id_els) > 0:
                parent_online_links = [x for x in parent_id_els]

                for parent_online_links_elm in parent_online_links:
                    online_link_handler = webLinkHandler(parent_online_links_elm)
                    parent_online_link = online_link_handler.create_web_link()
                    if parent_online_link["type"] == "catalogItemUrl":
                        parent_uri = parent_online_link["uri"]
                        idx = parent_uri.rfind('/')
                        parent_id = parent_uri[(idx+1):]
                    else:
                        # Add Element to list of onlink link elements processed later
                        non_parent_online_links.append(parent_online_links_elm)

        ea_els = self.get_xpath_text(xml_data, self.xpath_eainfo)
        if len(ea_els) > 0:
            self.browse_category_list = []
            self.browse_category_list.append("data")

        title = self.get_xpath_text(xml_data, self.xpath_title, single_item=True)
        description, summary = self.get_description(xml_data)
        purpose = self.get_xpath_text(xml_data, self.xpath_purpose, single_item=True)
        maintenance_freq = self.get_xpath_text(xml_data, self.xpath_main_update_freq, single_item=True)
        identifiers = self.get_identifiers(xml_data)
        spatial_dict = self.create_bounding_box(xml_data)
        citation_facets = self.create_citation_facets(xml_data)
        web_links = self.generate_web_links(xml_data, non_parent_online_links, source_url)
        tag_list = self.create_tags(xml_data)
        contact_list = self.generate_contact_info(xml_data)
        dates = self.get_publication_date_info(xml_data)
        time_periods = self.get_time_period_info(xml_data)
        for tp in time_periods:
            dates.append(tp)

        citation_facet_handler = citationHandler(facet_list=citation_facets)
        citation_str = citation_facet_handler.set_citation_string()

        # Generate a dictionary called item_data with all data generated from the xml file
        item_data = {}

        if len(identifiers) > 0:
            item_data["identifiers"] = identifiers
        if title:
            item_data["title"] = title
        if summary:
            item_data["summary"] = summary
        if description:
            item_data["body"] = description
        if citation_facets:
            item_data["citation"] = citation_str
        if purpose:
            item_data["purpose"] = purpose
        if maintenance_freq:
            item_data["maintenanceUpdateFrequency"] = maintenance_freq
        if parent_id is not None:
            item_data["parentId"] = parent_id
        if len(contact_list) > 0:
            item_data["contacts"] = contact_list
        if len(web_links) > 0:
            item_data["webLinks"] = web_links
        if len(tag_list) > 0:
            item_data["tags"] = tag_list
        if len(dates) > 0:
            item_data["dates"] = dates
        if len(spatial_dict) > 0:
            item_data["spatial"] = spatial_dict

        # Convert item_data dictionary to json and create a new json file
        #item_json = json.dumps(item_data)

        return item_data



