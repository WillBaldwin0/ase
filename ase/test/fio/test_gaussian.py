
# Tests of Gaussian I/O
from io import StringIO

import numpy as np
from ase.atoms import Atoms
from ase.io.gaussian import read_gaussian_in

import copy

# make an example input string with cartesian coords:
fd_cartesian = StringIO(u'''
%chk=example.chk
%Nprocshared=16
# N B3LYP/6-31G(d',p') ! ASE formatted method and basis
# Opt(Tight, MaxCyc=100)/Integral=Ultrafine, Freq

Gaussian input prepared by ASE

0 1
O1  -0.464   0.177   0.0
H1(iso=0.1134289259, NMagM=-8.89, ZEff=-1) -0.464   1.137   0.0
H2(iso=2, spin=1, QMom=1, RadNuclear=1, ZNuc=2)   0.441  -0.143   0.0
TV        10.0000000000        0.0000000000        0.0000000000
TV         0.0000000000       10.0000000000        0.0000000000
TV         0.0000000000        0.0000000000       10.0000000000

''')

# make an example input string with cartesian coords and a basis set
# definition:
fd_cartesian_basis_set = StringIO(u'''
%chk=example.chk
%Nprocshared=16
# N B3LYP/Gen ! ASE formatted method and basis
# Opt(Tight, MaxCyc=100)/Integral=Ultrafine, Freq

Gaussian input prepared by ASE

0 1
O1  -0.464   0.177   0.0
H1(iso=0.1134289259) -0.464   1.137   0.0
H2(iso=2)   0.441  -0.143   0.0

H     0
S    2   1.00
      0.5447178000D+01       0.1562849787D+00
      0.8245472400D+00       0.9046908767D+00
S    1   1.00
      0.1831915800D+00       1.0000000
****
O     0
S    6   1.00
      0.5472270000D+04       0.1832168810D-02
      0.8178060000D+03       0.1410469084D-01
      0.1864460000D+03       0.6862615542D-01
      0.5302300000D+02       0.2293758510D+00
      0.1718000000D+02       0.4663986970D+00
      0.5911960000D+01       0.3641727634D+00
SP   2   1.00
      0.7402940000D+01      -0.4044535832D+00       0.2445861070D+00
      0.1576200000D+01       0.1221561761D+01       0.8539553735D+00
SP   1   1.00
      0.3736840000D+00       0.1000000000D+01       0.1000000000D+01
****

''')

# make an example input string with a z-matrix:
fd_zmatrix = StringIO('''
%chk=example.chk
%Nprocshared=16
# T B3LYP
Gen
# opt(Tight, MaxCyc=100)/integral=Ultrafine, freq=ReadIso

Gaussian input with Z matrix

0 1
B 0 0.00 0.00 0.00
H 0 1.31 0.00 0.00
H 1 r1 2 a1
B 2 r1 1 a2 3 d1
H 1 r2 4 a3 2 d2
H 1 r2 4 a3 2 -d2
H 4 r2 1 a3 2 d2
H 4 r2 1 a3 2 -d2
Variables:
r1 1.31
r2 1.19
a1 97
a2 83
a3 120
d1 0
d2 90

300 1.0

0.1134289259 ! mass of second H

@basis-set-filename.gbs

''')


def test_readwrite_gaussian():
    '''Tests the read_gaussian_in and write_gaussian_in methods'''

    def check_atom_properties(atoms, atoms_new, params):
        assert np.all(atoms_new.numbers == atoms.numbers)
        assert np.allclose(atoms_new.get_masses(), atoms.get_masses())
        assert np.allclose(atoms_new.positions, atoms.positions, atol=1e-3)
        assert np.all(atoms_new.pbc == atoms.pbc)
        assert np.allclose(atoms_new.cell, atoms.cell)
        for key, array in atoms.arrays.items():
            if key[:8] == "gaussian":
                assert (atoms_new.arrays[key] == atoms.arrays[key]).all()

        new_params = atoms_new.calc.parameters
        matching_params = {k: new_params[k] for k in new_params
                           if k in params and new_params[k] == params[k]}

        if 'basis_set' in params:
            new_params = atoms_new.calc.parameters
            new_params_to_check = copy.deepcopy(new_params)
            params_to_check = copy.deepcopy(params)
            params_to_check['basis_set'] = params_to_check['basis_set'].split(
                '\n')
            params_to_check['basis_set'] = [line.strip()
                                            for line in
                                            params_to_check['basis_set']]
            new_params_to_check['basis_set'] = new_params_to_check[
                'basis_set'].strip().split('\n')
            matching_params = {k: new_params_to_check[k]
                               for k in new_params_to_check
                               if k in params_to_check and
                               new_params_to_check[k] == params_to_check[k]}

        assert (len(params) == len(matching_params))

    def test_write_gaussian(atoms, atoms_new):
        atoms_new.calc.label = 'gaussian_input_file'
        out_file = atoms_new.calc.label + '.com'

        atoms_new.calc.write_input(atoms_new)

        with open(out_file) as fd:
            atoms_written = read_gaussian_in(fd, True)
            check_atom_properties(atoms, atoms_written, params)

    # Tests reading a Gaussian input file with:
    # - Cartesian coordinates for the atom positions.
    # - ASE formatted method and basis
    # - PBCs
    # - All nuclei properties set
    # - Masses defined using nuclei properties

    positions = [[-0.464, 0.177, 0.0],
                 [-0.464, 1.137, 0.0],
                 [0.441, -0.143, 0.0]]
    cell = [[10., 0., 0.], [0., 10., 0.], [0., 0., 10.]]
    masses = [15.999, 0.1134289259, 2.01410177812]
    atoms = Atoms('OH2', cell=cell, positions=positions,
                  masses=masses)
    atoms.set_pbc(True)
    params = {'chk': 'example.chk', 'nprocshared': '16',
              'output_type': 'N', 'method': 'B3LYP',
              'basis': "6-31G(d',p')", 'opt': 'Tight, MaxCyc=100',
              'integral': 'Ultrafine', 'freq': None, 'charge': 0,
              'mult': 1}
    NMagM = np.array([None, '-8.89', None])
    ZEff = np.array([None, '-1', None])
    ZNuc = np.array([None, None, '2'])
    QMom = np.array([None, None, '1'])
    RadNuclear = np.array([None, None, '1'])
    Spin = np.array([None, None, '1'])
    atoms.new_array('gaussian_NMagM', NMagM)
    atoms.new_array('gaussian_ZEff', ZEff)
    atoms.new_array('gaussian_ZNuc', ZNuc)
    atoms.new_array('gaussian_QMom', QMom)
    atoms.new_array('gaussian_RadNuclear', RadNuclear)
    atoms.new_array('gaussian_Spin', Spin)
    atoms_new = read_gaussian_in(fd_cartesian, True)

    check_atom_properties(atoms, atoms_new, params)

    # Now we have tested reading the input, we can test writing it
    # and reading it back in.

    test_write_gaussian(atoms, atoms_new)

    # Tests reading a Gaussian input file with:
    # - Cartesian coordinates for the atom positions.
    # - ASE formatted method and basis
    # - Masses defined using nuclei properties

    atoms = Atoms('OH2', positions=positions, masses=masses)
    params['basis'] = 'gen'
    params['basis_set'] = '''H     0
S    2   1.00
    0.5447178000D+01       0.1562849787D+00
    0.8245472400D+00       0.9046908767D+00
S    1   1.00
    0.1831915800D+00       1.0000000
****
O     0
S    6   1.00
    0.5472270000D+04       0.1832168810D-02
    0.8178060000D+03       0.1410469084D-01
    0.1864460000D+03       0.6862615542D-01
    0.5302300000D+02       0.2293758510D+00
    0.1718000000D+02       0.4663986970D+00
    0.5911960000D+01       0.3641727634D+00
SP   2   1.00
    0.7402940000D+01      -0.4044535832D+00       0.2445861070D+00
    0.1576200000D+01       0.1221561761D+01       0.8539553735D+00
SP   1   1.00
    0.3736840000D+00       0.1000000000D+01       0.1000000000D+01
****'''
    atoms_new = read_gaussian_in(fd_cartesian_basis_set, True)
    check_atom_properties(atoms, atoms_new, params)

    # Now we have tested reading the input, we can test writing it
    # and reading it back in.

    test_write_gaussian(atoms, atoms_new)

    # Tests reading a Gaussian input file with:
    # - Z-matrix format for structure definition
    # - Variables in the Z-matrix
    # - Masses defined using 'ReadIso'
    # - Method and basis not formatted by ASE
    # - Basis file used instead of standard basis set.

    positions = np.array([
        [+0.000, +0.000, +0.000],
        [+1.310, +0.000, +0.000],
        [-0.160, +1.300, +0.000],
        [+1.150, +1.300, +0.000],
        [-0.394, -0.446, +1.031],
        [-0.394, -0.446, -1.031],
        [+1.545, +1.746, -1.031],
        [+1.545, +1.746, +1.031],
    ])
    masses = [None] * 8
    masses[1] = 0.1134289259
    atoms = Atoms('BH2BH4', positions=positions, masses=masses)

    params = {'chk': 'example.chk', 'nprocshared': '16', 'output_type': 'T',
              'b3lyp': None, 'gen': None, 'opt': 'Tight, MaxCyc=100',
              'freq': None, 'integral': 'Ultrafine', 'charge': 0, 'mult': 1,
              'temperature': '300', 'pressure': '1.0',
              'basisfile': '@basis-set-filename.gbs'}

    # Note that although the freq is set to ReadIso in the input text,
    # here we have set it to None. This is because when reading in a file
    # this option does not get saved to the calculator, it instead saves
    # the temperature, pressure, scale and masses separately.

    # Test reading the gaussian input
    atoms_new = read_gaussian_in(fd_zmatrix, True)

    check_atom_properties(atoms, atoms_new, params)

    # Now we have tested reading the input, we can test writing it
    # and reading it back in.

    test_write_gaussian(atoms, atoms_new)
