import re

class webLinkHandler:

    def __init__(self, url_string):
        self.url_string = url_string
        self.image_regex_pattern = re.compile('.(?:jpg|jpeg|tiff|gif|png)$', re.IGNORECASE)
        self.archive_regex_pattern = re.compile('.(?:pdf|doc|tif|zip|gz|tar|7z|laz)$', re.IGNORECASE)
        self.csw_portal_regex_pattern = re.compile('.*thumbnail.*', re.IGNORECASE)
        self.ogc_regex_pattern = re.compile('.*thumbnail.*', re.IGNORECASE)
        self.wms_regex_pattern = re.compile('.*service=wms.*', re.IGNORECASE)
        self.wfs_regex_pattern = re.compile('.*service=wfs.*', re.IGNORECASE)
        self.legend_regex_pattern = re.compile('.*request=getLegendGraphic.*', re.IGNORECASE)
        self.feature_info_regex_pattern = re.compile('.*request=getFeatureInfo.*', re.IGNORECASE)
        self.original_metadata_regex_pattern = re.compile('.*getxml=.*', re.IGNORECASE)
        self.catalog_item_regex_pattern = re.compile('.*sciencebase.gov/catalog/(item|folder).*')

    def create_web_link(self, rel="related", hidden=False):
        """
        Load all data for a web link into a dictionary based on a url string
        and use regex patterns to identify types of data in the url
        :param rel: Relationship info for a web link
        :param hidden: Boolean value for whether a web link is hidden
        :return: A dictionary with data for a web link
        """
        url_string = self.url_string.replace(" ", "%20")
        url_string = url_string.replace("[<|>]", "")
        new_link = {}
        last_dot_index = url_string.rfind(".")
        new_link["uri"] = url_string
        if last_dot_index > 0:
            extension = url_string[last_dot_index:]
            if self.image_regex_pattern.search(extension):
                new_link["type"] = "browseImage"
            elif self.archive_regex_pattern.search(extension):
                new_link["type"] = "download"
        if self.csw_portal_regex_pattern.search(url_string):
            new_link["type"] = "browseImage"
        if self.ogc_regex_pattern.search(url_string):
            new_link["type"] = "serviceCapabilitiesUrl"
            if self.wms_regex_pattern.search(url_string):
                new_link["title"] = "OGC WMS Capabilities"
            elif self.wfs_regex_pattern.search(url_string):
                new_link["type"] = "serviceWfsBackingUrl"
                new_link["title"] = "OGC WFS Capabilities"
            else:
                new_link["title"] = "OGC Capabilities"
        elif self.legend_regex_pattern.search(url_string):
            new_link["type"] = "serviceLegendUrl"
            new_link["title"] = "Legend"
        elif self.feature_info_regex_pattern.search(url_string):
            new_link["type"] = "serviceFeatureInfoUrl"
            new_link["title"] = "Feature Info"
        elif self.original_metadata_regex_pattern.search(url_string):
            new_link["type"] = "originalMetadata"
            new_link["title"] = "Original Metadata (XML)"
        elif self.catalog_item_regex_pattern.search(url_string):
            new_link["type"] = "catalogItemUrl"
            new_link["title"] = "Sciencebase catalog parent item"

        if "type" not in new_link:
            new_link["type"] = "webLink"

        new_link["rel"] = rel
        new_link["hidden"] = hidden

        return new_link

