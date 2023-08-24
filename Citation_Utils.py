class citationHandler:

    def __init__(self, element=None, facet_list=None):
        if element is not None:
            self.citation_element = element
        if facet_list is not None:
            self.citation_facet_list = facet_list

    def get_type_and_value(self, citation_type):
        """
        Gets the type and value from a citation element
        :param citation_type: The type of citation
        :return: A dictionary with the type and value
        """
        text_value = self.citation_element.text
        sb2_citation_part = {}
        if text_value:
            sb2_citation_part["type"] = citation_type
            sb2_citation_part["value"] = text_value

        return sb2_citation_part

    def get_publisher_and_place(self):
        """
        Gets citation info for a publication author and place
        :return: A list of dictionaries with metadata for a publication
        """
        publisher_and_place_info = []
        for sub_element in self.citation_element:
            if sub_element.tag == "pubplace":
                publication_place_value = sub_element.text
                if publication_place_value:
                    sb2_citation_part = {}
                    sb2_citation_part["type"] = "Publication Place"
                    sb2_citation_part["value"] = publication_place_value
                    publisher_and_place_info.append(sb2_citation_part)

            if sub_element.tag == "publish":
                publication_publisher_value = sub_element.text
                if publication_publisher_value:
                    sb2_citation_part = {}
                    sb2_citation_part["type"] = "Publisher"
                    sb2_citation_part["value"] = publication_publisher_value
                    publisher_and_place_info.append(sb2_citation_part)

        return publisher_and_place_info

    def get_publication_series_info(self):
        """
        Gets citation info for a publication series
        :return: A set of dictionaries with info on the publication series name and issue
        """
        name_value_dict = {}
        issue_value_dict = {}
        if self.citation_element.tag == "sername":
            series_name_value = self.citation_element.text
            if series_name_value:
                name_value_dict["type"] = "Publication Series Name"
                name_value_dict["value"] = series_name_value
        if self.citation_element.tag == "issue":
            # Series info: name and issue
            series_issue_value = self.citation_element.text
            if series_issue_value:
                issue_value_dict["type"] = "Publication Series Issue"
                issue_value_dict["value"] = series_issue_value

        return name_value_dict, issue_value_dict

    def get_larger_work_citation(self):
        """
        Larger work citation is a compound structure that 'contains' the citeinfo structure
        The online link is captured in the sb weblinks already so just capture the title
        :return: A list of dictionaries with metadata for a publication
        """
        larger_work_citations = []
        for sub_element in self.citation_element:
            if sub_element.tag == "title":
                larger_work_citation_title_value = sub_element.text
                if larger_work_citation_title_value:
                    sb2_citation_part = {}
                    sb2_citation_part["type"] = "Larger Work Title"
                    sb2_citation_part["value"] = larger_work_citation_title_value
                    larger_work_citations.append(sb2_citation_part)

        return larger_work_citations

    def set_citation_string(self):
        """
        Creates the citation string from the citation facet data
        :return: The citation string
        """
        originators = []
        citation_str = ""
        pubdate_str = ""
        pubtime_str = ""
        title_str = ""
        pub_sername_str = ""
        pub_serissue_str = ""
        publisher_str = ""
        onlink_str = ""
        onlink_str_2 = ""
        for facet in self.citation_facet_list:
            facet_parts = facet["parts"]
            for part in facet_parts:
                if part["type"] == "Originator":
                    originators.append(part["value"])
                if part["type"] == "Publication Date":
                    pubdate_str += part["value"] + ", "
                if part["type"] == "Publication Time":
                    pubtime_str += part["value"] + ", "
                if part["type"] == "Title":
                    title_str += part["value"] + ": "
                if part["type"] == "Publication Series Name":
                    pub_sername_str += part["value"] + ", "
                if part["type"] == "Publication Series Issue":
                    pub_serissue_str += part["value"] + ", "
                if part["type"] == "Publisher":
                    publisher_str += part["value"] + ", "
                if part["type"] == "Online Linkage":
                    onlink_str += part["value"] + ", "
                if part["type"] == "2nd Online Linkage":
                    onlink_str_2 += part["value"] + ", "
        if len(originators) > 0:
            len_originators = len(originators)
            for i in range(0, len_originators):
                origin_str = ""
                if i > 0 and i == (len_originators - 1):
                    origin_str += "and "
                origin_str += originators[i] + ", "
                citation_str += origin_str
        if pubdate_str:
            citation_str += pubdate_str
        if pubtime_str:
            citation_str += pubtime_str
        if title_str:
            citation_str += title_str
        if pub_sername_str:
            citation_str += pub_sername_str
        if pub_serissue_str:
            citation_str += pub_serissue_str
        if publisher_str:
            citation_str += publisher_str
        if onlink_str_2:
            citation_str += onlink_str_2
        if onlink_str:
            citation_str += onlink_str
        citation_str = citation_str[:-2]
        citation_str += "."

        return citation_str
