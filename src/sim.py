import numpy as np
from tqdm import tqdm
"""
Contains the classes used to represent a simulation
"""

class Sim:
    """Represents a single simulation. Field is initialized to all zeros.

    :param vacuum_permittivity: :math:`\epsilon_0`
    :param infinity_permittivity: :math:`\epsilon_\infty`
    :param vacuum_permeability: :math:`\mu_0`
    :param delta_t: :math:`\Delta t`
    :param delta_z: :math:`\Delta z`
    :param num_n: The number of time indexes
    :param num_i: The number of spatial indexes
    :param current: A field object that represents the current
    :param susceptibility: A susceptibility object
    :param initial_susceptibility: The initial susceptability. Eventually will be included in the susceptibility object.
    
    """
    
    def __init__(self, vacuum_permittivity, infinity_permittivity, vacuum_permeability, delta_t, delta_z, num_n, num_i, current_field, susceptibility, initial_susceptibility):
        self._vacuum_permittivity = vacuum_permittivity
        self._infinity_permittivity = infinity_permittivity
        self._vacuum_permeability = vacuum_permeability
        self._delta_t = delta_t
        self._delta_z = delta_z
        self._cfield = current_field
        self._susceptibility = susceptibility
        self._initial_susceptibility = initial_susceptibility
        self._num_n = num_n
        self._num_i = num_i
        self._efield = Field(num_n, num_i)
        self._hfield = Field(num_n, num_i)

        # Calculate simulation proportionality constants
        self._e_calc_term1_prop_coeff = self._infinity_permittivity/(self._infinity_permittivity + self._initial_susceptibility)
        self._e_calc_term2_prop_coeff = 1.0/(self._infinity_permittivity + self._initial_susceptibility)
        self._e_calc_term3_prop_coeff = self._delta_t/(self._vacuum_permittivity * self._delta_z * (self._infinity_permittivity + self._initial_susceptibility))
        self._e_calc_term4_prop_coeff = self._delta_t/(self._vacuum_permittivity * (self._infinity_permittivity + self._initial_susceptibility))

        self._h_calc_term2_prop_coeff = self._delta_t/(self._vacuum_permeability * self._delta_z)

        # Print constants
        print('Coefficients:\n=============')
        print(str(self._e_calc_term1_prop_coeff)[:13])
        print(str(self._e_calc_term2_prop_coeff)[:13])
        print(str(self._e_calc_term3_prop_coeff)[:13])
        print(str(self._e_calc_term4_prop_coeff)[:13])
        print(str(self._h_calc_term2_prop_coeff)[:13])
        print('=============')

    def get_vacuum_permittivity(self):
        """
        Gets :math:`\epsilon_0`
        
        :returns: :math:`\epsilon_0`
        """
        return self._vacuum_permittivity

    def get_infinity_permittivity(self):
        """
        Gets :math:`\epsilon_\infty`
        
        :returns: :math:`\epsilon_\infty`
        """
        return self._infinity_permittivity

    def get_vacuum_permeability(self):
        """
        Gets :math:`\mu_0`
        
        :returns: :math:`\mu_0`
        """
        return self._vacuum_permeability

    def get_delta_t(self):
        """
        Gets :math:`\Delta t`
        
        :returns: :math:`\Delta t`
        """
        return self._delta_t

    def get_delta_z(self):
        """
        Gets :math:`\Delta z`
        
        :returns: :math:`\Delta z`
        """
        return self._delta_z

    def get_num_n(self):
        """
        Gets the number of temporal indicies.
        
        :returns: The number of temporal indicies
        """
        return self._num_n

    def get_num_i(self):
        """
        Gets the number of spatial indicies.
        
        :returns: The number of spatial indicies
        """
        return self._num_i

    def get_efield(self):
        """
        Returns the E-field as a Field object.

        :return: The E-field as a Field object
        """
        return self._efield

    def get_hfield(self):
        """
        Returns the H-field as a Field object.

        :return: The H-field as a Field object
        """
        return self._hfield

    def get_cfield(self):
        """
        Returns the current field as a Field object.

        :return: The current field as a Field object
        """
        return self._cfield
        
    def simulate(self):
        """
        Executes the simulation.
        """
        self._efield.set_time_index(0) # Set the time index of the electric field to zero
        self._hfield.set_time_index(0) # Set the time index of the magnetic field to zero
        self._cfield.set_time_index(0) # Set the time index of the current field to zero
        # Simulate for one less step than the number of temporal indicies because initializing the fields to zero takes up the first temporal index
        for j in tqdm(range(self._num_n-1)):
            # Calculate the H and E fields
            self._calc_hfield()
            self._calc_efield()
            # Iterate the H and E, and current fields
            self._hfield.iterate()
            self._efield.iterate()
            self._iterate_cfield()
            

    def _calc_efield(self):
        r"""
        Calcualtes the electric field according to :math:`E^{i,n+1}=\frac{\epsilon_\infty}{\epsilon_\infty+\chi_e^0}E^{i,n}+\frac{1}{\epsilon_\infty+\chi_e^0}\psi^n-\frac{1}{\epsilon_0\left[\epsilon_\infty+\chi_e^0\right]}\frac{\Delta t}{\Delta z}\left[H^{i+1/2,n+1/2}-H^{i-1/2,n+1/2}\right]-\frac{\Delta tI_f}{\epsilon_0\left[\epsilon_\infty+\chi_e^0\right]}`. Note that the prior electric field array is located half a time index away at :math:`n-1` and the prior magnetic field array is located half a time index away at :math:`n-1/2`.
        """
        # Compute the values along the field
        for i in range(self._num_i):
            # TODO Can this calculation be done via vectors? This will likely improve efficiency
            term1 = self._e_calc_term1_prop_coeff * self._efield[i]
            term2 = self._e_calc_term2_prop_coeff * self.psi()
            term3 = self._e_calc_term3_prop_coeff * (self._hfield[i]-self._hfield[i-1])
            term4 = self._e_calc_term4_prop_coeff * self._current(i)
            self._efield[i] = term1 + term2 - term3 - term4
        
    def _calc_hfield(self):
        r"""
        Calculates the magnetic field according to :math:`H^{i+1/2,n+1/2}=H^{i+1/2,n-1/2}-\frac{1}{\mu_0}\frac{\Delta t}{\Delta z}\left[E^{i+1,n}-E^{i,n}\right]`. Note that the prior electric field array is located half a time index away at :math:`n-1/2` and the prior magnetic field array is located a whole time index away at :math:`n-1`.
        """
        # Compute the values along the field
        for i in range(self._num_i):
            # TODO Can this calculation be done via vectors? This will likely improve efficiency
            term1 = self._hfield[i]
            term2 = self._h_calc_term2_prop_coeff * (self._efield[i+1]-self._efield[i])
            self._hfield[i] = term1 - term2
        
    def _iterate_cfield(self):
        """
        Iterates the current field by simply increasing the temporal index by one.
        """
        prior_time = self._cfield.get_time_index()
        self._cfield.set_time_index(prior_time+1)

    def psi(self):
        """
        Calculates psi according to :math:`\psi^n=\sum^{n-1}_{m=0}E^{i,n-m}\Delta\chi_e^m` at the current time :math:`n` and position :math:`i`. Currently not implemented, and will simply return zero.

        :return: Zero
        """
        return 0

    def _current(self, i):
        """
        Gets the current at location :math:`i` and current time :math:`n` using the simulation's associated current field.

        :return: The current at location :math:`i` and current time :math:`n`
        """
        return self._cfield[i]

class Field:
    """
    Represents any field (i.e. electric, magnetic, current, susceptibility) using a 2D Numpy array. The zeroth axis represents increments in time and the first axis represents increments in space.

    :param num_n: The number of temporal indexes in the field
    :param num_i: The number of spatial indexes in the field
    :param field: A Numpy array that sets the field values in space and time. The field dimensions override num_n and num_i
    """

    def __init__(self, num_n=0, num_i=0, field=None):
        # Set the field time index to zero
        self._n = 0
        # Set the field temporal length to num_n
        self._num_n = num_n
        # Set the field spatial length to num_i
        self._num_i = num_i
        # Initialize field
        if field is None:
            # Initialize a zero field
            self._field = np.zeros((num_n, num_i), dtype=np.float64)
        else:
            # Set the field
            self._field = np.float64(field)
            # Extract field spatial and temporal indicies
            self._num_n, self._num_i = np.shape(field)

    def get_time_index(self):
        """
        Gets the current time index :math:`n`

        :return: The current time index :math:`n`
        """
        return self._n

    def set_time_index(self, n):
        """
        Sets the current time index to :math:`n`

        :param n: :math:`n`
        """
        # Check for that n is within the accepted range
        if(n < 0 or n >= self._num_n):
            raise IndexError('The n argument is of out of bounds')
        self._n = n

    def get_field(self, n=-1):
        """
        Gets the field at time :math:`n`, and the current time if :math:`n` is unspecified.

        :param n: :math:`n`
        :return: The field at time `n`
        """
        # If n is -1, return the current field
        if(n == -1):
            return self._field[self._n]
        # Check for that n is within the accepted range
        if(n < 0 or n >= self._num_n):
            raise IndexError('The n argument is of out of bounds')
        return self._field[n]

    def __getitem__(self, key):
        """
        Allows the [] operator to be used to get field values
        """
        return self.get_index(key)

    def get_index(self, i):
        """
        Gets the value of the field at the current time index :math:`n` and at the :math:`i` th spatial index. If the requested index is out of the field bounds, the returned value is zero.
        
        :param i: The spatial index of the field to access
        :return: The value of the field a the current time index :math:`n` and spatial index :math:`i`
        """
        # Check to see if the requested index is out of bounds, if so return zero
        if(i < 0 or i >= self._num_i):
            return np.float64(0)
        # Return the requested field
        return self._field[self._n,i]

    def __setitem__(self, key, value):
        """
        Allows the [] operator to be used to set field values
        """
        return self.set_index(key, value)

    def set_index(self, i, value):
        """
        Sets the value of the field at the current time index :math:`n` and at the :math:`i` th spatial index.
        
        :param i: The spatial index of the field to set
        :param value: The value to set at time index :math:`n` and spatial index :math:`i`
        """
        self._field[self._n,i] = np.float64(value)

    def set_field(self, nfield, n=-1):
        """
        Sets the field at time :math:`n`, and the current time if :math:`n` is unspecified. Raises a ValueError if the new field is not of the correct spatial length.

        :param nfield: The new field to append of length num_i
        """
        # Check for nfield length, raise error if necessary
        if(len(nfield) != self._num_i):
            raise ValueError('The nfield argument is of the incorrect length, found ' + str(len(nfield)) + ', expected ' + str(self._num_i))
        # If n is -1, set the current field
        if(n == -1):
            self._field[self._n] = nfield
        else:
            # Check for that n is within the accepted range
            if(n < 0 or n >= self._num_n):
                raise IndexError('The n argument is of out of bounds')
            # Set the new field value
            self._field[n] = nfield

    def iterate(self):
        """
        Copies the field at the current temporal location to the next temporal location, then iterates the temporal location.
        """
        # Check for that n is within the accepted range
        if(self._n + 1 >= self._num_n):
            raise IndexError('Cannot iterate as the end of the temporal index has been reached.')
        # Copy the current field to the next temporal index
        self._field[self._n+1] = self._field[self._n]
        # Iterate the temporal index
        self._n += 1


    def export(self):
        """
        Returns the Numpy array that contains the temporal (axis=0) and spatial values (axis=1) of the field.

        :return: A Numpy array
        """
        return self._field