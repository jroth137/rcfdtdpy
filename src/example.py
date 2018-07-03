from sim import Sim
from sim import Field
import vis
import numpy as np
"""
A module that shows how to use the sim module to prepare and run RC-FDTD simulations.
"""

def prep_sim():
    """
    Used to prepare the simulation object
    """

if __name__ == '__main__':
    # Prepare constants
    vacuum_permittivity = 4*np.pi*(10.0**(-7))
    infinity_permittivity = 0
    vacuum_permability = 8.854187817 * (10**(-12))
    delta_z = 3e4
    delta_t = 3e-4

    # Prepare current field
    cfield = Field(500000, 5000)
    cfield[200] = 0.500

    # Prepare and perform simulation
    s = Sim(vacuum_permittivity,infinity_permittivity,vacuum_permability,delta_t,delta_z,500000,5000,cfield,0,0)
    s.simulate()

    # Export simulation result
    arr = s.get_efield().export()

    # Visualize result
    print(np.shape(arr))
    vis.contor_plot(arr, delta_z, delta_z)