##############################################################################################################################################
#   Filename:       MyProg.py
#   Summary:        This program is a circuit simulator that calculates the electrical parameters of a specified circuit based on
#                   a provided configuration file. 
#                   It supports frequency-dependent impedance calculations and can handle different types of components.
#
#   Description:    MyProg.py loads data from an input file using  DataExtract to create the frequecny sweep,
#                   component details, and circuit terms. It handles both linear and logarithmic frequency sweeps
#                   and supports different component types through the Impedance and FreqDepImpedence classes. 
#                   The program attempts to construct a circuit using the Circ class, calculate all electrical
#                   parameters, and export the results using the CircResultsExporter class. Error handling includes
#                   generating an empty output file if any part of the process fails due to improper inputs 
#                   or during the calculation process.
#
#   Version:        v3.08
#   Date:           24/04/2024
#   Authors:        Joshua O Poole
##############################################################################################################################################

import sys
import numpy
import math
import pandas as pd
import re
import cmath
import csv

from DataExtract import DataExtract
from Impedence import Impedance, FreqDepImpedence, ComponentConnectionException, ComponentTypeException
from Circ import Circ
from CircResultsExporter import CircResultsExporter


##################################################################################################
#Main
##################################################################################################


def errorexporter(file_path):
    # If an error is encountered that results in the circuit provided
    # not being simulatable, then an empty csv file is to be exported.
    print("An empty CSV file is being exported")
    with open(file_path, 'w', newline='') as output_file:
            output_file.write() 


# Store the command line arguments 
if len(sys.argv) != 3:
    print("Usage: python MyProg.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
Txt_Data = DataExtract(input_file)
# attempt to generate any frequency sweep
try:
    # attempt to generate a linear frequency sweep by accesing the 'Fstart', 'Fend', 'Nfreqs' keys
    try:
        freq = numpy.linspace(Txt_Data.formatted_Term_Values['Fstart'], Txt_Data.formatted_Term_Values['Fend'], Txt_Data.formatted_Term_Values['Nfreqs'])
    # This will occur when the 'Fstart', 'Fend', 'Nfreqs' keys do not exist
    # In this case attempt to generate a log frequency sweep by accesing the 'LFstart', 'LFend', 'Nfreqs' keys
    except Exception:
        freq = numpy.logspace(numpy.log10(Txt_Data.formatted_Term_Values['LFstart']), numpy.log10(Txt_Data.formatted_Term_Values['LFend']), Txt_Data.formatted_Term_Values['Nfreqs'])
# This will occur when there is no frequecny information to access.
except Exception:
    errorexporter(output_file)

# Iterate through each line in formatted_Circ_Values, each of which represent a component
frequencies = freq
components = []
for component_data in Txt_Data.formatted_Circ_Values:
    # attempt to generate any component
    try:
        # attempt to generate a component as an instance of Impedance
        try:
            comp = Impedance(
                Pin1=component_data['n1'], 
                Pin2=component_data['n2'], 
                Value=component_data['value'], 
                Type=component_data['type']
            )
        # This will occr when a component cannot be represented as an instance of Impedance
        # In this case # attempt to generate a component as an instance of FreqDepImpedence
        except ComponentTypeException:
            comp = FreqDepImpedence(
                Pin1=component_data['n1'], 
                Pin2=component_data['n2'], 
                Value=component_data['value'], 
                Type=component_data['type'], 
                Freq=frequencies
            )
    # This will occur when a component is misconnected (n1 = n2)
    except ComponentConnectionException:
        # In this case simply skip this component!
        continue
    components.append(comp)

# Is any components have been made
if len(components) != 0:
    # attempt to perform outputs calculations and exportation
    try:
        circuit = Circ(components_list= components, Freq= frequencies, LoadRes= Txt_Data.formatted_Term_Values['RL'], Vth= Txt_Data.formatted_Term_Values['VT'], Rs= Txt_Data.formatted_Term_Values['RS'])
        param = Txt_Data.formatted_Outputs
        exporter = CircResultsExporter(circuit, param)
        exporter.export_to_csv(output_file)
    except Exception:
        errorexporter(output_file)
else:
    errorexporter(output_file)
