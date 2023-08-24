import re
import datetime

class datetimeHandler:

    def __init__(self, datetime_string):
        self.datetime_string = datetime_string

    def test_date_string(self):
        """
        Check a date string object from the xml file to make sure it is in a valid date format
        :return: boolean value for whether the date string has a valid format, and the format
        """
        date_formats = {'8_char_format': '^\d{8}$',
                        '%Y-%m-%d': '^\d{4}-(\d{2}|\d{1})-(\d{2}|\d{1})$',
                        '6_char_format': '^\d{6}$',
                        '%Y-%m': '^\d{4}-(\d{2}|\d{1})$',
                        '%Y': '^\d{4}$'}

        is_valid_format = False
        date_format = ""
        df_keys = list(date_formats.keys())
        for key in df_keys:
            df_regex_pattern = re.compile(date_formats[key])
            df_matcher = df_regex_pattern.match(self.datetime_string)
            if df_matcher:
                is_valid_format = True
                date_format = key
                if date_format == '8_char_format':
                    if int(self.datetime_string[:2]) >= 13:
                        date_format = '%Y%m%d'
                    else:
                        date_format = '%m%d%Y'
                if date_format == '6_char_format':
                    if int(self.datetime_string[:2]) >= 13:
                        date_format = '%Y%m'
                    else:
                        date_format = '%m%Y'

        return is_valid_format, date_format

    def test_time_string(self):
        """
        Check a time string object from the xml file to make sure it is in a valid date format
        :return: boolean value for whether the time string has a valid format, and the format
        """
        time_formats = {'%H%M%S%f%z': '/^\d{8}-\d{4}$/',
                        '%H:%M:%S.%f%z': '/^\d{2}:\d{2}:\d{2}.\d{2}-\d{4}$/',
                        '%H%M%S%f': '/^\d{8}$/',
                        '%H:%M:%S.%f': '/^\d{2}:\d{2}:\d{2}.\d{2}$/',
                        '%H%M%S%z': '/^\d{6}-\d{4}$/',
                        '%H:%M:%S%z': '/^\d{2}:\d{2}:\d{2}-\d{4}$/',
                        '%H%M%S': '/^\d{6}$/',
                        '%H:%M:%S': '/^\d{2}:\d{2}:\d{2}$/',
                        '%H%M': '/^\d{4}$/',
                        '%H:%M': '/^\d{2}:\d{2}$/',
                        '%H': '/^\d{2}$/'}
        is_valid_format = False
        time_format = ""
        tf_keys = list(time_formats.keys())
        for key in tf_keys:
            tf_regex_pattern = re.compile(time_formats[key])
            tf_matcher = tf_regex_pattern.match(self.datetime_string)
            if tf_matcher:
                is_valid_format = True
                time_format = key
        return is_valid_format, time_format

    def convert_date_format(self, input_format):
        """
        converts date format to one of the acceptable sbjson date formats
        if it is not already in one of those formats
        :param input_format: the format of the input date string
        :return: the output date string in the proper date format
        """
        output_date_string = self.datetime_string
        if input_format in ['%Y%m', '%m%Y']:
            date_string = datetime.datetime.strptime(self.datetime_string, input_format)
            output_date_string = date_string.strftime('%Y-%m')
        if input_format in ['%Y%m%d', '%m%d%Y']:
            date_string = datetime.datetime.strptime(self.datetime_string, input_format)
            output_date_string = date_string.strftime('%Y-%m-%d')

        return output_date_string

    def convert_time_format(self, input_format):
        """
        converts time format to one of the acceptable sbjson time formats
        if it is not already in one of those formats
        :param input_format: the format of the input time string
        :return: the output time string in the proper time format
        """
        output_time_string = self.datetime_string
        if input_format == '%H%M':
            time_string = datetime.datetime.strptime(self.datetime_string, input_format)
            output_time_string = time_string.strftime('%H:%M')
        if input_format in ['%H%M%S%f%z', '%H:%M:%S.%f%z', '%H%M%S%f', '%H:%M:%S.%f', '%H%M%S%z', '%H:%M:%S%z', '%H%M%S']:
            time_string = datetime.datetime.strptime(self.datetime_string, input_format)
            output_time_string = time_string.strftime('%H:%M:%S')

        return output_time_string





