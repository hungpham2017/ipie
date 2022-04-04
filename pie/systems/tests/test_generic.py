import os
import unittest
import numpy
import pytest
from mpi4py import MPI
from pie.systems.generic import Generic
from pie.hamiltonians.generic import Generic as HamGeneric
from pie.hamiltonians.utils import get_generic_integrals
from pie.utils.testing import generate_hamiltonian


@pytest.mark.unit
def test_real():
    numpy.random.seed(7)
    nmo = 17
    nelec = (4,3)
    h1e, chol, enuc, eri = generate_hamiltonian(nmo, nelec, cplx=False)
    sys = Generic(nelec=nelec) 
    ham = HamGeneric(h1e=numpy.array([h1e,h1e]),
                  chol=chol.reshape((-1,nmo*nmo)).T.copy(),
                  ecore=enuc)
    assert sys.nup == 4
    assert sys.ndown == 3
    assert numpy.trace(h1e) == pytest.approx(9.38462274882365)


@pytest.mark.unit
def test_complex():
    numpy.random.seed(7)
    nmo = 17
    nelec = (5,3)
    h1e, chol, enuc, eri = generate_hamiltonian(nmo, nelec, cplx=True, sym=4)
    sys = Generic(nelec=nelec) 
    ham = HamGeneric(h1e=numpy.array([h1e,h1e]),
                  chol=chol.reshape((-1,nmo*nmo)).T.copy(),
                  ecore=enuc)
    assert sys.nup == 5
    assert sys.ndown == 3
    assert ham.nbasis == 17

@pytest.mark.unit
def test_write():
    numpy.random.seed(7)
    nmo = 13
    nelec = (4,3)
    h1e, chol, enuc, eri = generate_hamiltonian(nmo, nelec, cplx=True, sym=4)
    sys = Generic(nelec=nelec) 
    ham = HamGeneric(h1e=numpy.array([h1e,h1e]),
                  chol=chol.reshape((-1,nmo*nmo)).T.copy(),
                  ecore=enuc)
    ham.write_integrals(nelec)

@pytest.mark.unit
def test_read():
    numpy.random.seed(7)
    nmo = 13
    nelec = (4,3)
    h1e_, chol_, enuc_, eri_ = generate_hamiltonian(nmo, nelec, cplx=True, sym=4)
    from pie.utils.io import write_qmcpack_dense
    chol_ = chol_.reshape((-1,nmo*nmo)).T.copy()
    write_qmcpack_dense(h1e_, chol_, nelec, nmo,
                        enuc=enuc_, filename='hamil.h5',
                        real_chol=False)
    filename = 'hamil.h5'
    nup, ndown = nelec
    comm = None
    hcore, chol, h1e_mod, enuc = get_generic_integrals(filename,
                                                       comm=comm,
                                                       verbose=False)
    sys = Generic(nelec=nelec) 
    ham = HamGeneric(h1e=hcore,
                  chol=chol,
                  ecore=enuc)
    assert ham.ecore == pytest.approx(0.4392816555570978)
    assert ham.chol_vecs.shape == chol_.shape # now two are transposed
    assert len(ham.H1.shape) == 3
    assert numpy.linalg.norm(ham.H1[0]-h1e_) == pytest.approx(0.0)
    assert numpy.linalg.norm(ham.chol_vecs-chol_) == pytest.approx(0.0) # now two are transposed

@pytest.mark.unit
def test_shmem():
    numpy.random.seed(7)
    nmo = 13
    nelec = (4,3)
    comm = MPI.COMM_WORLD
    h1e_, chol_, enuc_, eri_ = generate_hamiltonian(nmo, nelec, cplx=True, sym=4)
    from pie.utils.io import write_qmcpack_dense
    chol_ = chol_.reshape((-1,nmo*nmo)).T.copy()
    write_qmcpack_dense(h1e_, chol_, nelec, nmo,
                        enuc=enuc_, filename='hamil.h5',
                        real_chol=False)
    filename = 'hamil.h5'
    nup, ndown = nelec
    from pie.utils.mpi import get_shared_comm
    shared_comm = get_shared_comm(comm, verbose=True)
    hcore, chol, h1e_mod, enuc = get_generic_integrals(filename,
                                                       comm=get_shared_comm,
                                                       verbose=False)
    # system = Generic(h1e=hcore, chol=chol, ecore=enuc,
    #                  h1e_mod=h1e_mod, nelec=nelec,
    #                  verbose=False)
    # print("hcore.shape = ", hcore.shape)
    sys = Generic(nelec=nelec) 
    ham = HamGeneric(h1e=hcore, h1e_mod = h1e_mod,
                  chol=chol.copy(),
                  ecore=enuc)
    
    assert ham.ecore == pytest.approx(0.4392816555570978)
    assert ham.chol_vecs.shape == chol_.shape # now two are transposed
    assert len(ham.H1.shape) == 3
    assert numpy.linalg.norm(ham.H1[0]-h1e_) == pytest.approx(0.0)
    assert numpy.linalg.norm(ham.chol_vecs-chol_) == pytest.approx(0.0) # now two are transposed

def teardown_module():
    cwd = os.getcwd()
    files = ['hamil.h5']
    for f in files:
        try:
            os.remove(cwd+'/'+f)
        except OSError:
            pass

if __name__ == '__main__':
    test_write()
    test_read()
    test_shmem()
