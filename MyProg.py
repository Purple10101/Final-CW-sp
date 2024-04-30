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
    print("An empty CSV file is being exported")
    with open(file_path, 'w', newline='') as output_file:
            output_file.write() 

# Usage


if len(sys.argv) != 3:
    print("Usage: python MyProg.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
Txt_Data = DataExtract(input_file)
try:
    try:
        freq = numpy.linspace(Txt_Data.formatted_Term_Values['Fstart'], Txt_Data.formatted_Term_Values['Fend'], Txt_Data.formatted_Term_Values['Nfreqs'])
    except Exception:
        freq = numpy.logspace(numpy.log10(Txt_Data.formatted_Term_Values['LFstart']), numpy.log10(Txt_Data.formatted_Term_Values['LFend']), Txt_Data.formatted_Term_Values['Nfreqs'])
except Exception:
    errorexporter(output_file)

frequencies = freq

components = []
for component_data in Txt_Data.formatted_Circ_Values:
    try:
        try:
            comp = Impedance(
                Pin1=component_data['n1'], 
                Pin2=component_data['n2'], 
                Value=component_data['value'], 
                Type=component_data['type']
            )
        except ComponentTypeException:
            comp = FreqDepImpedence(
                Pin1=component_data['n1'], 
                Pin2=component_data['n2'], 
                Value=component_data['value'], 
                Type=component_data['type'], 
                Freq=frequencies
            )
    except ComponentConnectionException:
        continue
    components.append(comp)

if len(components) != 0:
    try:
        circuit = Circ(components_list= components, Freq= frequencies, LoadRes= Txt_Data.formatted_Term_Values['RL'], Vth= Txt_Data.formatted_Term_Values['VT'], Rs= Txt_Data.formatted_Term_Values['RS'])
        param = Txt_Data.formatted_Outputs
        exporter = CircResultsExporter(circuit, param)
        exporter.export_to_csv(output_file)
    except Exception:
        errorexporter(output_file)
else:
    errorexporter(output_file)
