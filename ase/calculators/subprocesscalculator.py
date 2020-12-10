import sys
from abc import ABC, abstractmethod
import pickle
from subprocess import Popen, PIPE
from ase.calculators.calculator import Calculator, all_properties
from ase.calculators.singlepoint import SinglePointDFTCalculator


class PackedCalculator(ABC):
    """Portable calculator for use via PythonSubProcessCalculator.

    This class allows creating and talking to a calculator which
    exists inside a different process, possibly with MPI or srun.

    Use this when you want to use ASE mostly in serial, but run some
    calculations in a parallel Python environment.

    Most existing calculators can be used this way through the
    NamedPackedCalculator implementation.  To customize the behaviour
    for other calculators, write a custom class inheriting this one.

    Example::

      from ase.build import bulk

      atoms = bulk('Au')
      pack = NamedPackedCalculator('emt')

      with pack.calculator() as atoms.calc:
          energy = atoms.get_potential_energy()

    The computation takes place inside a subprocess which lives as long
    as the with statement.
    """

    @abstractmethod
    def unpack_calculator(self) -> Calculator:
        """Return the calculator packed inside.

        This method will be called inside the subprocess doing
        computations."""

    def calculator(self) -> 'PythonSubProcessCalculator':
        """Return a PythonSubProcessCalculator for this calculator.

        The subprocess calculator wraps a subprocess containing
        the actual calculator, and computations are done inside that
        subprocess."""
        return PythonSubProcessCalculator(self)


class NamedPackedCalculator(PackedCalculator):
    """PackedCalculator implementation which works with standard calculators.

    This works with calculators known by ase.calculators.calculator."""
    def __init__(self, name, kwargs=None):
        self._name = name
        if kwargs is None:
            kwargs = {}
        self._kwargs = kwargs

    def unpack_calculator(self):
        from ase.calculators.calculator import get_calculator_class
        cls = get_calculator_class(self._name)
        return cls(**self._kwargs)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._name}, {self._kwargs})'


class PythonSubProcessCalculator(Calculator):
    """Calculator for running calculations in external processes.

    TODO: This should work with arbitrary commands including MPI stuff.

    This calculator runs a subprocess wherein it sets up an
    actual calculator.  Calculations are forwarded through pickle
    to that calculator, which returns results through pickle."""
    implemented_properties = list(all_properties)

    def __init__(self, calc_input):
        super().__init__()

        self.proc = None
        self.calc_input = calc_input

    def set(self, **kwargs):
        if hasattr(self, 'proc'):
            raise RuntimeError('No setting things for now, thanks')

    def _send(self, obj):
        pickle.dump(obj, self.proc.stdin)
        self.proc.stdin.flush()

    def _recv(self):
        return pickle.load(self.proc.stdout)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__,
                               self.calc_input)

    def __enter__(self):
        assert self.proc is None
        self.proc = Popen([sys.executable, '-m', __name__],
                          stdout=PIPE, stdin=PIPE)
        self._send(self.calc_input)
        return self

    def __exit__(self, *args):
        self._send('stop')
        self.proc.wait()
        self.proc = None

    def _run_calculation(self, atoms, properties, system_changes):
        self._send('calculate')
        self._send((atoms, properties, system_changes))

    def calculate(self, atoms, properties, system_changes):
        Calculator.calculate(self, atoms, properties, system_changes)
        # We send a pickle of self.atoms because this is a fresh copy
        # of the input, but without an unpicklable calculator:
        self._run_calculation(self.atoms.copy(), properties, system_changes)
        results = self._recv()
        self.results.update(results)


def main():
    # We switch stdout so stray print statements won't interfere with outputs:
    binary_stdout = sys.stdout.buffer
    sys.stdout = sys.stderr

    def recv():
        return pickle.load(sys.stdin.buffer)

    def send(obj):
        pickle.dump(obj, binary_stdout)
        binary_stdout.flush()

    pack = recv()
    calc = pack.unpack_calculator()

    while True:
        instruction = recv()
        if instruction == 'stop':
            break
        elif instruction != 'calculate':
            raise ValueError('Bad instruction: {}'.format(instruction))

        atoms, properties, system_changes = recv()

        # Again we need formalization of the results/outputs, and
        # a way to programmatically access all available properties.
        # We do a wild hack for now:
        calc.results.clear()
        # If we don't clear(), the caching is broken!  For stress.
        # But not for forces.  What dark magic from the depths of the
        # underworld is at play here?
        calc.calculate(atoms=atoms, properties=properties,
                       system_changes=system_changes)
        results = calc.results
        send(results)


if __name__ == '__main__':
    main()
