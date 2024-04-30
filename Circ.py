##############################################################################################################################################
#   Filename:       Circ.py
#   Summary:        Order the coupe of componets into a 'circuit' and model it as an ABCD matrix to calculate many peramiters.
#   Description:    This file contains the Circ class which takes as argument a list of components, all defined terms (VT,RL,RS and range).
#                   It first orders the comopnents by there input nodes and calculates a cascade ABCD matrix by fetching component ABCD mats
#                   for inducidual components at each frequecny.
#                   With this ABCD mat that represents the wole network, it then calculates all required outputs.
#                   There is also a method that aranges this data in an order that is defined as argument
#                   
#
#   Version:        v3.01
#   Date:           22/04/2024
#   Authors:        Joshua O Poole
##############################################################################################################################################

import numpy
import math
import cmath

class Circ:

    """
    Class with argument attributes components_list: list(component), Freq: list(float), LoadRes: int, Vth: int, Rs: int.
    Orders the list of components and calculates cascade network ABCD matrix for the circuit defined by the list of components.
    Uses this matrix and the other arguments to calculate V1: float, V2: float, I1: float, I2: float, Zin: float, Zout: float,
    Pin: float, Pout: float, Ai: float, Av: float on initialization.

    :def Order_components:
        Returns the ordered components list by the 'In_node' key.
        
        :param components_list: list(component) - List of components to order.
        :return: components_list_ordered: list(component) - Ordered list of components.

    :def Vin_calc, Iin_calc:
        Uses the class argument attributes to calculate the input measurements.
        
        :param Vth: float - Thevenin voltage.
        :param Rs: float - Source resistance.
        :param Zin: dict(float, float) - Input impedance as a dictionary.
        :return: ABCD: dict(float, float) - ABCD parameters calculated.

    :def Z_GEN:
        Uses the class argument attributes and the calculated matrix dictionary to calculate the impedance of the network.
        
        :param LoadRes: int - Load resistance.
        :param Rs: int - Source resistance.
        :param Cascade_ABCD_MAT: dict(float, numpy.array) - Cascade matrix for each frequency.
        :return: Zin: dict(float, float) - Input impedance for each frequency.
                Zout: dict(float, float) - Output impedance for each frequency.

    :def MAT_GEN:
        For each frequency in Freq, cascade the component ABCD matrices and store in a dictionary where frequency maps to a cascade matrix.
        
        :param Freq: list(float) - List of frequencies.
        :param components_list: list(component) - List of components.
        :return: Cascade_ABCD_MAT: dict(float, numpy.array) - Dictionary mapping frequencies to cascade matrices.

    :def get_Ordered_Outputs:
        Convert calculated attributes to dB if specified in the outputs section of the text file.
        Do this by accessing the order argument which is a dict(Value type e.g. 'Vin', measurement e.g. dBV).
        Return a dictionary where value types map to the calculated values.
        
        :input: [All calculated outputs] - List of all outputs calculated by the class.
        :output: Outputs: dict(string, float) - Dictionary of outputs possibly converted to dB.

    """
    def __init__(self, components_list, Freq, LoadRes, Vth, Rs):
        self.components_list = components_list
        self.Freq = Freq
        self.LoadRes = LoadRes
        self.Vth = Vth
        self.Rs = Rs
        self.conversionDict = {
            'p': 'e-12',
            'n': 'e-9',
            'u': 'e-6',
            'm': 'e-3',
            'k': 'e3',
            'M': 'e6',
            'G': 'e9'
        }
        self.components_list_Ordored = self.Order_components()
        self.cascade_ABDC_mat = self.MAT_GEN()

        self.Zin, self.Zout = self.Z_GEN()
        self.Vin = self.Vin_CALC()
        self.Iin = self.Iin_CALC()
        self.Vout, self.Iout = self.calculate_VoutIout()
        self.Pin = self.Pin_CALC()
        self.Pout = self.Pout_CALC()
        self.Av = self.Av_CALC()
        self.Ai = self.Ai_CALC()
        self.Ap = self.Ap_CALC()
        

    def Order_components(self):

        # Simply sort by in_node whilst also ensuring all are non zero
        # This shoulnt be the case, but this code is here to accept this case
        return sorted(self.components_list, key=lambda x: (x.In_node, not (x.Pin1 == 0 or x.Pin2 == 0)))
            
    def MAT_GEN(self):

        """
        This method takes the list of ordered components and cascades them by performing
        inorder multiplication on each components matrix for each frequecny
        """

        MAT = {}
        # Iterate through each frequecny
        for F in self.Freq:
            # set current_MAT to the identity matrix
            current_MAT = numpy.array([[1,0],[0,1]])
            # Iterate through each component
            for component in self.components_list_Ordored:
                # set ABCD equal to component.MAT_GEN() at frequecny F
                ABCD = component.MAT_GEN(F)
                # multiply current matrix by ABCD
                current_MAT = current_MAT @ ABCD
            # store this matrix in a dict where freq maps to matrix
            MAT[F] = current_MAT
        return MAT
    
    def Vin_CALC(self):
        V1 = {}
        # Iterate through each frequecny
        for F in self.Freq:
            # store result in a dict where freq maps to V1 value
            V1[F] = self.Vth * (self.Zin[F]/(self.Zin[F] + self.Rs))
        return V1
    
    def Iin_CALC(self):
        I1 = {}
        # Iterate through each frequecny
        for F in self.Freq:
            # store result in a dict where freq maps to I1 value
            I1[F] = self.Vin[F]/self.Zin[F]
        return I1
    
    def Pin_CALC(self):
        Pin = {}
        # Iterate through each frequecny
        for F in self.Freq:
            V1 = self.Vin[F]
            I1 = self.Iin[F]
            # store result in a dict where freq maps to Pin value
            Pin[F] = V1 * I1.conjugate()
        return Pin
    
    def Pout_CALC(self):
        Pout = {}
        # Iterate through each frequecny
        for F in self.Freq:
            V2 = self.Vout[F]
            I2 = self.Iout[F]
            # store result in a dict where freq maps to Pin value
            Pout[F] = V2 * I2.conjugate()
        return Pout
    
    def Av_CALC(self):
        Av = {}
        # Iterate through each frequecny
        for F in self.Freq:
            A, B = self.cascade_ABDC_mat[F][0, 0], self.cascade_ABDC_mat[F][0, 1]
            Z_L = self.LoadRes
            # store result in a dict where freq maps to Av value
            Av[F] = 1 / (A + B / Z_L)
        return Av

    def Ai_CALC(self):
        Ai = {}
        # Iterate through each frequecny
        for F in self.Freq:
            # store result in a dict where freq maps to Ai value
            Ai[F] = self.Iout[F]/self.Iin[F]
        return Ai
    
    def Ap_CALC(self):
        Ap = {}
        # Iterate through each frequecny
        for F in self.Freq:
            # store result in a dict where freq maps to Ap value
            Ap[F] = self.Pout[F]/self.Pin[F]
        return Ap

    
    def Z_GEN(self):
        Zin = {}
        Zout = {}
        # Iterate through each frequecny
        for F in self.Freq:
            A, B, C, D = self.cascade_ABDC_mat[F][0, 0], self.cascade_ABDC_mat[F][0, 1], self.cascade_ABDC_mat[F][1, 0], self.cascade_ABDC_mat[F][1, 1]
            Z_L = self.LoadRes
            Z_S = self.Rs
            # store result in a dict where freq maps to Zin and Zout values
            Zin[F] = (A * Z_L + B) / (C * Z_L + D)
            Zout[F] = (D * Z_S + B) / (C * Z_S + A)
        return Zin, Zout
    
    def calculate_VoutIout(self):
        V2 = {}
        I2 = {}
        # Iterate through each frequecny
        for F in self.Freq:
            ABCD = self.cascade_ABDC_mat[F]
            A, B = ABCD[0, 0], ABCD[0, 1]
            V1 = self.Vin[F]
            Iout = V1/(A*self.LoadRes+B)
            Vout = self.LoadRes * Iout
            # store result in a dict where freq maps to V2 and I2 values
            V2[F], I2[F] = Vout, Iout
        return V2, I2
    
    def get_Ordered_Outputs(self, order):
        Outputs = {}

        # Iterate through each frequecny
        for F in self.Freq:
            Inter = {}
            # Iterate through each output specifed in the .net file
            for param, unit in order.items():
                # Split the peramiter by whitespaces 
                parts = param.split(" ")
                # Isolate the first part as the second part is the unit
                param_raw = parts[0]
                # fetch the artibute whos name is specified by param_raw
                value = getattr(self, param_raw, None)
                if value is None:
                    # Skip if attribute does not exist
                    continue  
                if 'dB' in unit:
                    # Define dB_multiplier based on the presence of specific keywords in param
                    if any(keyword in param for keyword in ['Pout', 'Pin', 'Zin', 'Zout', 'Ap']):
                        dB_multiplier = 10
                    else:
                        dB_multiplier = 20
                    dB_removed = unit.replace("dB", "")
                    # In case where dB in unit check for power of 10 prefix in unit
                    if any(dB_removed.startswith(key) for key in self.conversionDict):
                        for key in self.conversionDict.keys():
                            if dB_removed.startswith(key):
                                Converted_value = value[F]/float('1'+self.conversionDict[key])
                        mag_dB = dB_multiplier * math.log10(abs(Converted_value)) if abs(Converted_value) > 0 else -float('inf')
                        phase_rad = cmath.phase(Converted_value)
                        Inter[param] = {'Mag': mag_dB, 'Phase': phase_rad}
                    else:
                        mag_dB = dB_multiplier * math.log10(abs(value[F])) if abs(value[F]) > 0 else -float('inf')
                        phase_rad = cmath.phase(value[F])
                        Inter[param] = {'Mag': mag_dB, 'Phase': phase_rad}
                else:
                    Inter[param] = value[F]
            Outputs[F] = Inter

        return Outputs

    
