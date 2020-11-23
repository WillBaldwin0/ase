"""Example, in order to run you must place a pseudopotential 'Na.psf' in
the folder"""

from ase.units import Ry, eV
from ase.calculators.siesta import Siesta
from ase.calculators.siesta.siesta_lrtddft import siesta_lrtddft
from ase.build import molecule
import numpy as np
import matplotlib.pyplot as plt

# Define the systems
CH4 = molecule('CH4')

# enter siesta input
CH4.calc = Siesta(
    mesh_cutoff=150*Ry,
    basis_set='DZP',
    energy_shift=(10*10**-3) * eV,
    fdf_arguments={
        'COOP.Write': True,
        'WriteDenchar': True,
        'PAO.BasisType': 'split',
        'DM.Tolerance': 1e-4,
        'DM.MixingWeight': 0.01,
        'XML.Write': True})

e = CH4.get_potential_energy()
freq=np.arange(0.0, 25.0, 0.05)

lr = siesta_lrtddft(label="siesta", jcutoff=7, iter_broadening=0.15,
                    xc_code='LDA,PZ', tol_loc=1e-6, tol_biloc=1e-7)
pmat = lr.get_polarizability(freq)

# plot polarizability
fig = plt.figure(1)
ax1 = fig.add_subplot(111)
ax1.plot(freq, pmat[0, 0, :].imag)

ax1.set_xlabel(r"$\omega$ (eV)")
ax1.set_ylabel(r"Im($P_{xx}$) (au)")
ax1.set_title(r"Non interacting")

fig.tight_layout()
plt.show()
