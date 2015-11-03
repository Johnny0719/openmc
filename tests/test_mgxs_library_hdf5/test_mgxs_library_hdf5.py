#!/usr/bin/env python

import os
import sys
import glob
import hashlib
import h5py
sys.path.insert(0, os.pardir)
from testing_harness import PyAPITestHarness
import openmc
import openmc.mgxs


class MGXSTestHarness(PyAPITestHarness):
    def _build_inputs(self):

        # The openmc.mgxs module needs a summary.h5 file
        self._input_set.settings.output = {'summary': True}

        # Generate inputs using parent class routine
        super(MGXSTestHarness, self)._build_inputs()

        # Initialize a two-group structure
        energy_groups = openmc.mgxs.EnergyGroups(group_edges=[0, 0.625e-6, 20.])

        # Initialize MGXS Library for a few cross section types
        self.mgxs_lib = openmc.mgxs.Library(self._input_set.geometry.geometry)
        self.mgxs_lib.by_nuclide = False
        self.mgxs_lib.mgxs_types = ['transport', 'nu-fission',
                                    'nu-scatter matrix', 'chi']
        self.mgxs_lib.energy_groups = energy_groups
        self.mgxs_lib.domain_type = 'material'
        self.mgxs_lib.build_library()

        # Initialize a tallies file
        self._input_set.tallies = openmc.TalliesFile()
        self.mgxs_lib.add_to_tallies_file(self._input_set.tallies, merge=False)
        self._input_set.tallies.export_to_xml()

    def _get_results(self, hash_output=False):
        """Digest info in the statepoint and return as a string."""

        # Read the statepoint file.
        statepoint = glob.glob(os.path.join(os.getcwd(), self._sp_name))[0]
        sp = openmc.StatePoint(statepoint)

        # Read the summary file.
        summary = glob.glob(os.path.join(os.getcwd(), 'summary.h5'))[0]
        su = openmc.Summary(summary)
        sp.link_with_summary(su)

        # Load the MGXS library from the statepoint
        self.mgxs_lib.load_from_statepoint(sp)
        
        # Export the MGXS Library to an HDF5 file
        self.mgxs_lib.build_hdf5_store(directory='.')

        # Open the MGXS HDF5 file
        f = h5py.File('mgxs.h5', 'r')

        # Build a string from the datasets in the HDF5 file
        outstr = ''
        for domain in self.mgxs_lib.domains:
            for mgxs_type in self.mgxs_lib.mgxs_types:
                outstr += 'domain={0} type={1}\n'.format(domain.id, mgxs_type)
                key = 'material/{0}/{1}/average'.format(domain.id, mgxs_type)
                outstr += str(f[key][...]) + '\n'
                key = 'material/{0}/{1}/std. dev.'.format(domain.id, mgxs_type)
                outstr += str(f[key][...]) + '\n'
        
        # Close the MGXS HDF5 file
        f.close()

        # Hash the results if necessary
        if hash_output:
            sha512 = hashlib.sha512()
            sha512.update(outstr.encode('utf-8'))
            outstr = sha512.hexdigest()

        return outstr


    def _cleanup(self):
        super(MGXSTestHarness, self)._cleanup()
        f = os.path.join(os.getcwd(), 'tallies.xml')
        if os.path.exists(f): os.remove(f)
        f = os.path.join(os.getcwd(), 'mgxs.h5')
        if os.path.exists(f): os.remove(f)


if __name__ == '__main__':
    harness = MGXSTestHarness('statepoint.10.*', True)
    harness.main()