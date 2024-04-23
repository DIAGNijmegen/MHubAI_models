"""
---------------------------------------------------------
Mhub / DIAG - Run Module for the PICAI baseline Algorithm
---------------------------------------------------------

---------------------------------------------------------
Author: Sil van de Leemput
Email:  sil.vandeleemput@radboudumc.nl
---------------------------------------------------------
"""

import json
import sys
from pathlib import Path

from mhubio.core import Instance, InstanceData, IO, Module, ValueOutput, ClassOutput, Meta


CLI_PATH = Path(__file__).parent / "cli.py"


@ValueOutput.Name('prostate_cancer_likelihood')
@ValueOutput.Label('ProstateCancerLikelihood')
@ValueOutput.Type(float)
@ValueOutput.Description('Likelihood of case-level prostate cancer.')
class ProstateCancerLikelihood(ValueOutput):
    pass


class PicaiBaselineRunner(Module):

    @IO.Instance()
    @IO.Input('in_data_t2', 'mha:mod=mr:type=t2w', the='input T2 weighted prostate MR image')
    @IO.Input('in_data_adc', 'mha:mod=mr:type=adc', the='input ADC prostate MR image')
    @IO.Input('in_data_hbv', 'mha:mod=mr:type=hbv', the='input HBV prostate MR image')
    @IO.Output('cancer_likelihood_json', 'cspca-case-level-likelihood.json', "json", bundle='model', the='output JSON file with PICAI baseline prostate cancer likelihood')
    @IO.Output('cancer_lesion_detection_map', 'cspca-detection-map.mha', "mha:mod=dm", bundle='model', the='output detection map of clinically significant prostate cancer lesions in 3D, where each voxel represents a floating point in range [0,1]')
    @IO.OutputData('cancer_likelihood', ProstateCancerLikelihood, the='PICAI baseline prostate cancer likelihood')
    def task(self, instance: Instance, in_data_t2: InstanceData, in_data_adc: InstanceData, in_data_hbv: InstanceData, cancer_likelihood_json: InstanceData, cancer_lesion_detection_map: InstanceData, cancer_likelihood: ProstateCancerLikelihood) -> None:
        # build command (order matters!)
        cmd = [
            sys.executable,
            str(CLI_PATH),
            in_data_t2.abspath,
            in_data_adc.abspath,
            in_data_hbv.abspath,
            cancer_likelihood_json.abspath,
            cancer_lesion_detection_map.abspath,
        ]

        # run the command as subprocess
        self.subprocess(cmd, text=True)

        # Extract cancer likelihood value from cancer_likelihood_file
        if not Path(cancer_likelihood_json.abspath).is_file():
            raise FileNotFoundError(f"Output file {cancer_likelihood_json.abspath} could not be found!")

        with open(cancer_likelihood_json.abspath, "r") as f:
            cancer_lh = float(json.load(f))

        if not (isinstance(cancer_lh, (float, int)) and (0.0 <= cancer_lh <= 1.0)):
            raise ValueError(f"Cancer likelihood value should be between 0 and 1, found: {cancer_lh}")

        # Output the predicted values
        cancer_likelihood.value = cancer_lh
