from ase import Atoms
from ase.calculators.crystal import CRYSTAL
import os


geom = Atoms('C2',
             cell=[[0.21680326E+01, -0.12517142E+01,  0.000000000E+00],
                   [0.00000000E+00,  0.25034284E+01,  0.000000000E+00],
                   [0.00000000E+00,  0.00000000E+00,  0.50000000E+03]],
             positions=[(-0.722677550504, -1.251714234963, 0.),
                        (-1.445355101009, 0.,  0.)],
             pbc=[True, True, False])

geom.set_calculator(CRYSTAL(label='graphene',
                            guess=True,
                            xc='PBE',
                            kpts=(1, 1, 1),
                            otherkeys=['scfdir', 'anderson',
                                       ['maxcycles', '500'],
                                       ['toldee', '6'],
                                       ['tolinteg', '7 7 7 7 14'],
                                       ['fmixing', '95']]
                            ))

final_energy = geom.get_potential_energy()
assert abs(final_energy + 2063.13266758) < 1.0

files = ['SCFOUT.LOG', 'INPUT', 'optc1', 'ERROR',
         'FORCES.DAT', 'dffit3.dat', 'OUTPUT']

for file in files:
    try:
        os.remove(file)
    except OSError:
        pass

dir = os.getcwd()
fort = os.listdir(dir)
for file in fort:
    if file.startswith("fort."):
        os.remove(os.path.join(dir, file))
