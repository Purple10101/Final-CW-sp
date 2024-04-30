##############################################################################################################################################
#   Filename:       Impedence.py
#   Summary:        Calculates ABCD matrix in case of Impdence or a frequecny specified ABCD matrix in case of FreqDepImpedence.
#   Description:    Is passed all the relevant component data such as pin configuration, value and type and then determines which
#                   terminal is the 'input' terminal and calulates the impedance at each frequecny in case of FreqDepImpedence.
#                   In case of Impdence this is not necesary. The components value or Z[frequecny] is then used to caluacate 
#                   its representative ABCD matrix.
#
#
#   Version:        v3.01
#   Date:           21/04/2024
#   Authors:        Joshua O Poole
##############################################################################################################################################


import numpy
import math

class ComponentConnectionException(Exception):
    def __init__(self):
        # Initialize the Exception base class with a custom message
        print("Comonent misconnected and subsequently removed")
        super().__init__()

class ComponentTypeException(Exception):
    def __init__(self):
        # Initialize the Exception base class with a custom message
        super().__init__()

class Impedance:

    """
    Class with argument attributes `Pin1:int`, `Pin2:int`, `Value:float`, `Type:string`.
    Calculates and stores attributes `In_node` and `ABCD`.
    These attributes are calculated and assigned on initialization.

    :def MAT_GEN:
        Identifies if the component being represented is in shunt or series.
        Uses the generic ABCD matrix to represent an individual component.

        :param Pin1: int - First pin identifier.
        :param Pin2: int - Second pin identifier.
        :param Value: float - The value of the component.
        :param Type: string - Type of the component (shunt or series).
        :return: ABCD - numpy.array representing the ABCD matrix.

    :def Node_ID:
        Identifies which of `n1` and `n2` (`Pin1`, `Pin2`) is the input node.

        :param Pin1: int - First pin identifier.
        :param Pin2: int - Second pin identifier.
        :return In_node: int - Identifier of the input node.
    """
    def __init__(self, Pin1, Pin2, Value, Type):
        self.Type = Type
        self.Pin1 = Pin1
        self.Pin2 = Pin2
        self.Value = Value
        self.Is_valid()
        self.In_node = self.Node_ID()

    def get_Pin1(self):
        return self.Pin1

    def get_Pin2(self):
        return self.Pin2

    def get_Value(self):
        return self.Value
    
    def Is_valid(self):
        if(self.Pin1 == self.Pin2):
            raise ComponentConnectionException

    def MAT_GEN(self, F):

        """
        Generates The ABCD matrix that represnts the component
        The component type determines the nature of the matrix.
        The frequency argument is presnet to avoid collisions in the later inheritence.

        >>> comp1 = Impedance(1,2,50,'R')
        >>> comp1.MAT_GEN(10)
        array([[ 1, 50],
               [ 0,  1]])
        >>> comp2 = Impedance(2,0,0.02,'G')
        >>> comp2.MAT_GEN(10)
        array([[1.  , 0.  ],
               [0.02, 1.  ]])
        """

        # In case where the component is a resistor representyed by type R
        if self.Type == "R":
            # In case where the componment is in shunt
            if self.Pin1 == 0 or self.Pin2 == 0:
                ABCD = numpy.array([[1, 0], [1/self.Value, 1]])
            # In case where the componment is in series
            else:
                ABCD = numpy.array([[1, self.Value], [0, 1]])
            return ABCD
        # In case where the component is a ammitence representyed by type G
        elif self.Type == "G":
            # In case where the componment is in shunt
            if self.Pin1 == 0 or self.Pin2 == 0:
                ABCD = numpy.array([[1, 0], [self.Value, 1]])
            # In case where the componment is in series
            else:
                ABCD = numpy.array([[1, 1/self.Value], [0, 1]])
            return ABCD
        
    def Node_ID(self):

        """
        Identifies which of the 2 nodes the signal is input to.
        This is important for ordering components when they are assembled into a circuit.
        
        All components are first instanciated as type Impedence
        This method allows for compopnets of type "L" and "C" to be identified.

        >>> comp1 = Impedance(1,2,50,'R')
        >>> comp1.Node_ID()
        1
        >>> comp2 = Impedance(2,0,0.02,'G')
        >>> comp2.Node_ID()
        2
        >>> comp3 = Impedance(10,9,0.02,'G')
        >>> comp3.Node_ID()
        9
        """

        # Identify weather a component is of an exceptable type "R" or "G"
        if self.Type not in ["R", "G"]:
            # In this case raise a custom ComponentTypeException()
            # signifying that the component is frequecny dependent
            raise ComponentTypeException()
        # Identify weather a component have a zero node
        if min(self.Pin1,self.Pin2) == 0:
            # In this case the larger of the two nodes is the input node
            in_node = max(self.Pin1,self.Pin2)
        else:
            # else the smaller of the two is the input
            in_node = min(self.Pin1,self.Pin2)
        return in_node

    


##################################################################################################
#FreqDepImpedence
##################################################################################################

class FreqDepImpedence(Impedance):

    """
    Class with attributes `Pin1:int`, `Pin2:int`, `Value:float`, `Type:string`, `Freq:list[float]`.
    Calculates and stores attributes `In_node` impedance (dict) and `ABCD` (dict).
    Frequencies map to impedances, which can then be used to calculate the ABCD matrix at that frequency.
    The impedance attribute is calculated and assigned on initialization, but the matrices are not.

    :def Z_GEN:
        Returns the impedance at all frequencies in `Freq` as a dictionary where frequency maps to impedance.

        :input Value: float - The value attribute of the component.
        :input Freq: list[float] - List of frequencies.
        :output Impedances: dict(float, float) - Dictionary mapping frequencies to their respective impedances.

    :def MAT_GEN:
        Identifies if the component being represented is in shunt or series.
        Uses the generic ABCD matrix to represent an individual component at any given frequency by accessing the `Impedances` dictionary.
        This method will not be called in the `__init__` and will be accessible outside the class.

        :input Pin1: int - First pin identifier.
        :input Pin2: int - Second pin identifier.
        :input Value: float - The value of the component.
        :input Type: string - Type of the component (shunt or series).
        :input Frequency: float - Frequency at which the matrix is to be generated.
        :output ABCD: dict(float, float) - Dictionary representing the ABCD parameters at the specified frequency.

    :def Node_ID:
        Identifies which of `Pin1` and `Pin2` is the input node.

        :input Pin1: int - First pin identifier.
        :input Pin2: int - Second pin identifier.
        :output In_node: int - Identifier of the input node.
    """
    def __init__(self, Pin1, Pin2, Value, Type, Freq):
        super().__init__(Pin1, Pin2, Value, Type)
        self.Freq = Freq
        self.In_node = self.Node_ID()
        self.Z = self.Z_GEN()

    def get_Type(self):
        return self.Type

    def Z_GEN(self):

        """
        Generates The impedence that represnts the component for all frequencies.
        Output is a lookup table of impedences with the range Freq

        >>> comp1 = FreqDepImpedence(1,2,0.003,'L',[10,10000])
        >>> comp1.Z_GEN()
        {10: 0.1884955592153876j, 10000: 188.4955592153876j}
        >>> comp2 = FreqDepImpedence(1,2,0.003,'C',[1,1984])
        >>> comp2.Z_GEN()
        {1: -53.05164769729845j, 1984: -0.026739741782912527j}
        """

        Z = {}
        # In case where the component is of type "C"
        if self.Type == "C":
            # for each frequency, store the impednece in a dictonary with freqeuncy as a key
            for F in self.Freq:
                Z[F] = numpy.complex128(1/(1j*2*math.pi*F*self.Value))
        elif self.Type == "L":
            # for each frequency, store the impednece in a dictonary with freqeuncy as a key
            for F in self.Freq:
                Z[F] = numpy.complex128(1j*2*math.pi*F*self.Value)
        return Z

    def MAT_GEN(self, F):

        """
        Generates an ABCD matrix at a given argument frequecny.

        >>> comp1 = FreqDepImpedence(1,2,0.003,'L',[10,10000])
        >>> comp1.MAT_GEN(10)
        array([[1.+0.j        , 0.+0.18849556j],
               [0.+0.j        , 1.+0.j        ]])
        >>> comp2 = FreqDepImpedence(1,0,0.003,'C',[1,1984])
        >>> comp2.MAT_GEN(1984)
        array([[ 1. +0.j        ,  0. +0.j        ],
               [-0.+37.39751895j,  1. +0.j        ]])
        """

        ABCD = []
        # In case where the component is in shunt
        if self.Pin1 == 0 or self.Pin2 == 0:
            ABCD = numpy.array([[1, 0], [1/self.Z[F], 1]])
        # In case where the component is in series
        else:
            ABCD = numpy.array([[1, self.Z[F]], [0, 1]])
        return ABCD
    
    def Node_ID(self):
        if self.Type not in ["L", "C"]:
            raise ComponentTypeException
        # Identify weather a component have a zero node
        if min(self.Pin1,self.Pin2) == 0:
            # In this case the larger of the two nodes is the input node
            in_node = max(self.Pin1,self.Pin2)
        else:
            # else the smaller of the two is the input
            in_node = min(self.Pin1,self.Pin2)
        return in_node
    


if __name__ == "__main__":
    import doctest
    doctest.testmod()
