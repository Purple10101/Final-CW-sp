##############################################################################################################################################
#   Filename:       DataExtract.py
#   Summary:        Takes the .net input file and stores the data within in a processable medium.
#   Description:    This file contains the DataExtract class which takes the file name of the .net file as argument.
#                   The contense of the file is saved in a string, and split by the delimmiters.
#                   Conversion from power of 10 prefixes is now implimented!
#                   Support for both dB and linear displays is now active!
#                   Each section is then parsed and processed.
#                   There are many helper functions that compliment the primary read_file method which didctates the folw of operation.
#                   Docstrings at the start of helper functions contain doctests.
#                   This iteration fixes a bug that was able to occur when incorrect component syntax was provided.
#
#                   This version of the class stores outputs in a list as opsosed to a dict to avoid collisions
#                   Therfore supporting multiple of the same mesurmewnt to be displayed
#
#   Version:        v3.04
#   Date:           19/04/2024
#   Authors:        Joshua O Poole
##############################################################################################################################################



import pandas as pd
import re


class DataExtract:
    """
    Class with argument attribute file_name. This class reads a file and breaks down the resultant string into sections defined by delimiters.
    It uses regular expressions to convert patterns like "n1=1" into a dictionary entry {'n1': 1} and repeats this for each section while handling errors appropriately.

    :def read_file:
        Opens and reads the content from [file_name], removes comments, breaks up [content], and formats each line into a list element.
        It processes each section, storing the results in appropriate data structures.

        :param file_name: str - The name of the file to be read.
        :return: formatted_circuit: list(dict(str, float)) - A list of dictionaries containing formatted circuit data.
                formatted_terms: dict(str, float) - Dictionary containing formatted terms.
                formatted_output: dict(str, str) - Dictionary containing formatted output.

    :def remove_comments:
        Removes lines beginning with '#' from the input string. Lines in the string are delimited by '\n'.

        :param text: str - Text from which comments are to be removed.
        :return: filtered_text: str - Text after comments have been removed.

    :def parse_section:
        Uses the delimiter '\n' to break down the string into lines, storing each line in a list.

        :param section: str - The section of the text to parse.
        :return: data: list(str) - List of strings, each representing a line from the input section.

    :def node_helper:
        Stores data from regex matches identified as nodes.

        :param matches: list(str) - List of strings that match node patterns.
        :return: node_dict: dict - Dictionary of node data.

    :def value_helper:
        Stores data from regex matches identified as type=value, with support for prefixes.

        :param matches: list(str) - List of strings that match value patterns.
        :return: val_dict: dict - Dictionary of value data.

    :def process_[circuit,terms,output]_section:
        Processes data from regex matches and stores it in appropriate data structures.

        :param data: list(str) - List of strings containing data for either the circuit, terms, or output.
        :return: formatted_[terms,output]_data: dict(str, [int, str]) - Dictionary containing processed terms or output data.
                formatted_circuit_data: list(dict(str, float)) - List of dictionaries containing processed circuit data.
"""
    def __init__(self, file_name):
        self.file_name = file_name
        self.conversionDict = {
            'p': 'e-12',
            'n': 'e-9',
            'u': 'e-6',
            'm': 'e-3',
            'k': 'e3',
            'M': 'e6',
            'G': 'e9'
        }
        self.read_file()

    def read_file(self):
        with open(self.file_name, 'r') as file:
            content = file.read()
            # content is the raw text contained in the input file
        Real_Content = self.remove_comments(content)
        # Remove lines that begin with '#'
        try:
            circuit_section = Real_Content.split('<CIRCUIT>')[1].split('</CIRCUIT>')[0]
            terms_section = Real_Content.split('<TERMS>')[1].split('</TERMS>')[0]
            output_section = Real_Content.split('<OUTPUT>')[1].split('</OUTPUT>')[0]
            # Split the content by sections
        except IndexError:
            # This will occur when a delimiter is missing
            # The spec and model files mean that the program must not terminate but an empty file must be exported
            # hence the assignation of sections with empty lists
            print("Missing required input information (Some delimiting text was not found)")
            circuit_section = []
            terms_section = []
            output_section = []
        try:
            # Get each section into the form of a list where each line is stored at an index
            circuit_data = self.parse_section(circuit_section)
            terms_data = self.parse_section(terms_section)
            output_data = self.parse_section(output_section)
            # Process each section using regEx and strore golablly in dic for acces outside of class object
            self.formatted_Circ_Values = self.process_circuit_data(circuit_data)
            self.formatted_Term_Values = self.process_terms_data(terms_data)
            self.formatted_Outputs = self.process_output_data(output_data)
        except Exception:
            # This will occur when any contense within the sections cannot be processed as intended
            # E.g. there is a string ('BREXIT') where a float (3.18e-9) should be
            # The spec and model files mean that the program must not terminate but an empty file must be exported
            # hence the assignation of sections with empty lists
            self.formatted_Circ_Values = [{}]
            self.formatted_Term_Values = {}
            self.formatted_Outputs = {}

    def remove_comments(self, text):
        """
        Remove lines begining with '#'

        >>> extract = DataExtract('b_RC.net')
        >>> extract.remove_comments('Hello\\n#Hello')
        'Hello'
        >>> extract.remove_comments('#Hello\\n#Hello\\nR=50')
        'R=50'
        >>> extract.remove_comments('#L=3.18e-9\\n#C=3.18e-12')
        ''
        """
        # Split the text into lines and filter out those that start with '#'
        lines = text.splitlines()
        filtered_lines = [line for line in lines if not line.lstrip().startswith('#')]
        # Join the filtered lines back into a single string
        return '\n'.join(filtered_lines)
    
    def parse_section(self, section):
        """
        Store each line in the string as an entry in a list

        >>> extract = DataExtract('b_RC.net')
        >>> extract.parse_section('Hello\\nHello')
        ['Hello', 'Hello']
        >>> extract.parse_section('Hello\\nHello\\nR=50')
        ['Hello', 'Hello', 'R=50']
        >>> extract.parse_section('\\n')
        ['']
        """
        data = []
        # Iterate through each line of the text and add the line to the data list
        for line in section.strip().split('\n'):
                data.append(line)
        return data
    

    def node_helper(self, matches):
        node_dict = {}
        for name, value in matches:
            node_dict[name] = int(value)
        return node_dict
    
    def value_helper(self, matches):
        val_dict = {}
        for name, value in matches:
            try: 
            # Store the component value and type and store each of them in the variables dict
                compVal = float(value)
                type = str(name)
                val_dict['type'] = type
                val_dict['value'] = compVal
            except ValueError:
                # Attempt this conversion again using the powers of 10 prefix
                try:
                    count = 0
                    for fix, exp in self.conversionDict.items():
                        if fix in value:
                            count +=1
                            new_value = value + exp
                            new_value = new_value.replace(fix,'')
                            val_dict['value'] = float(new_value)
                            val_dict['type'] = str(name)
                    if count ==0:
                        raise ValueError
                except ValueError:
                    #This will occur if a component has an incompatable type or value
                    print(f"Value for '{name}' is not in supported format: '{value}'")
                    component_data = []
                    return component_data
        return val_dict



    def process_circuit_data(self, circuit_data):
        """
        Store the circuit data in list of dict
        each dict represents one component

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_circuit_data(['n1=1 n2=2 R=50','n1=2 n2=0 C=5e-9'])
        [{'n1': 1, 'n2': 2, 'type': 'R', 'value': 50.0}, {'n1': 2, 'n2': 0, 'type': 'C', 'value': 5e-09}]
        >>> extract.process_circuit_data(['n1=1 n2=2 R=50','n1=2 n2=0 C=error'])
        Value for 'C' is not in supported format: 'error'
        []
        """
        component_data = []
        # Define regular extression that matches the formatting of the input file
        pattern_nodes = r'(\w+)=(\S+)'
        pattern_value = r'(\w+)=(\d+(?:\.\d+)?(?:e[+-]?\d+)?[numkMG]?)'

        # Iterate through each component in the circuit
        # Components can be defined as a line in the circuit section
        for component in circuit_data:
            # Isolate all matches in the component line
            pattern = r'^(.*?)(\s\w+=(?:\d+(?:\.\d+)?(?:e[+-]?\d+)?|[a-zA-Z]+)\s?[numkMG]?)$'
            match = re.search(pattern, component)
            nodes_string = match.group(1)
            value_string = match.group(2).replace(' ','')
            matches_nodes = re.findall(pattern_nodes, nodes_string)
            matches_value = re.findall(pattern_value, value_string)
            if matches_nodes and matches_value:
                # Iterate through each match of the RegEx
                nodes = self.node_helper(matches_nodes)
                val = self.value_helper(matches_value)
                combined_dict = {**nodes, **val}
                component_data.append(combined_dict)
            else:
                #This will occur if a component has an incompatable type or value
                print(f"Value in '{component}' is not in supported format")
                component_data = []
                return component_data
        return component_data

    def process_terms_data(self,terms_data):
        """
        Store the terms data in a dict

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_terms_data(['VT=5 RS=50','RL=50','Fstart=10.0 Fend=10e+6 Nfreqs=50'])
        {'VT': 5, 'RS': 50, 'RL': 50, 'Fstart': 10.0, 'Fend': 10000000.0, 'Nfreqs': 50}
        >>> extract.process_terms_data(['Vth=50','Fstart=10.0 Fend=10e+6 Nfreqs=error'])
        Value for 'Nfreqs' is not in supported format: 'error'
        {}
        """
        # Define regular extression that matches the formatting of the input file
        pattern = r'(\b\w+\b)=(\S+)'
        # Join the section together so we dont need to iterate through each line
        # Remove this later!!!!
        combined_string = ' '.join(terms_data)
        # Isolate all matches in the string
        matches = re.findall(pattern, combined_string)
        variables = {}
        # Iterate through each match of the RegEx
        for name, value in matches:
            try:
                # Try to store match in variables dict as string-int
                variables[name] = int(value)
            except ValueError:
                # This will occur when value cannot be cast to type int
                try:
                    # Try to store match in variables dict as string-float
                    variables[name] = float(value)
                except ValueError:
                    # This will occur when value cannot be cast to type int or folat
                    # This means that an error is present in the input file
                    # The spec and model files mean that the program must not terminate but an empty file must be exported
                    # hence the return of an empty dict
                    print(f"Value for '{name}' is not in supported format: '{value}'")
                    return {}
        return variables
    
    def process_output_data(self,output_data):
        """
        Store the circuit data in list of dict
        each dict represents one component

        >>> extract = DataExtract('b_RC.net')
        >>> extract.process_output_data(['Hello hi', 'Farewell bye'])
        {'Hello': 'hi', 'Farewell': 'bye'}
        """
        # Define regular extression that matches the formatting of the input file
        pattern = r'(\w+)\s*(\w+)?'
        # Isolate all matches in the string cast of the section
        matches = re.findall(pattern, str(output_data))
        variables = {}
        # Iterate through matches
        for name, unit in matches:
                # Store match in variables dict as string-string
                variables[name+" "+unit] = str(unit)
        return variables



if __name__ == "__main__":
    import doctest
    doctest.testmod()
