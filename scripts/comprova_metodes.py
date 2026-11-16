"""Comprovo els canvis petits amb senyals que conec."""
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parent.parent
checks = []
with tempfile.TemporaryDirectory(prefix='p2-metodes-') as name:
    temp = Path(name)
    def execute(x, rate, flags=()):
        audio, output = temp/'test.wav', temp/'test.vad'
        sf.write(audio, x, rate, subtype='PCM_16')
        result = subprocess.run([str(root/'bin/vad'), '-i', str(audio), '-o', str(output), '-v', *flags],
                                capture_output=True, text=True, check=True)
        labels = [(float(a), float(b), c) for a, b, c in (line.split() for line in output.read_text().splitlines())]
        return labels, result.stdout

    for rate in (8000, 16000, 48000):
        n = rate//100
        def blocks(values):
            x = np.repeat(np.array(values, dtype=float), n)
            x[1::2] *= -1
            return x
        x = blocks([.001]*20 + [.1]*30 + [.001]*30)
        original, _ = execute(x, rate)
        assert original == [(0., .2, 'S'), (.2, .5, 'V'), (.5, .8, 'S')]
        delayed, _ = execute(x, rate, ['--sense-retroces'])
        assert delayed == [(0., .27, 'S'), (.27, .66, 'V'), (.66, .8, 'S')]
        immediate, _ = execute(x, rate, ['--veu=1', '--silenci=1', '--sense-retroces'])
        assert immediate == original
        _, text = execute(x, rate, ['--alfa=0'])
        thresholds = [float(line.split()[-1]) for line in text.splitlines()[8:]]
        assert max(thresholds) == min(thresholds)
        _, text = execute(blocks([.5]+[0.]*28), rate, ['--treu-pic'])
        assert abs(float(text.splitlines()[8].split()[-1])-(-94.06)) < .001
        one_dip = blocks([.001]*20 + [.1]*4 + [.001] + [.1]*4 + [.001]*30)
        labels, _ = execute(one_dip, rate, ['--permet-baixada'])
        assert [(a,b) for a,b,c in labels if c=='V'] == [(.2,.29)]
        two_dips = blocks([.001]*20 + [.1]*4 + [.001]*2 + [.1]*4 + [.001]*30)
        labels, _ = execute(two_dips, rate, ['--permet-baixada'])
        assert all(c=='S' for _,_,c in labels)
        labels, _ = execute(x+.125, rate, ['--treu-dc'])
        assert labels == original
        # Un nivell entre els dos llindars no comença veu, però manté la que ja hi havia.
        between = .001*10**(5.4/20)
        labels, _ = execute(blocks([.001]*20+[between]*30+[.001]*30), rate,
                            ['--alfa=0', '--histeresi=1'])
        assert all(c=='S' for _,_,c in labels)
        labels, _ = execute(blocks([.001]*20+[.1]*10+[between]*20+[.001]*30), rate,
                            ['--alfa=0', '--histeresi=1'])
        assert [(a,b) for a,b,c in labels if c=='V'] == [(.2,.5)]
        all_flags = ['--treu-pic', '--permet-baixada', '--treu-dc', '--histeresi=1', '--sense-retroces']
        labels, text = execute(np.full(rate//2, .25), rate, all_flags)
        assert labels == [(0.,.5,'S')]
        assert all(np.isfinite(float(line.split()[2])) for line in text.splitlines())
        for length in (max(1,n//2), 4*n):
            labels, _ = execute(np.zeros(length), rate, all_flags)
            assert labels == [(0., round(length/rate,6), 'S')]
        checks.append(f'OK: {rate} Hz: duracions, retrocés, soroll fix, pic, baixada, DC, histèresi i tots junts.')
    for option in ('--inici=0', '--inici=1 --treu-pic', '--veu=nan', '--veu=1.5',
                   '--silenci=-1', '--alfa=nan', '--alfa=1.1', '--histeresi=6', '--histeresi=-1'):
        result = subprocess.run([str(root/'bin/vad'), '-i', str(temp/'test.wav'), '-o', str(temp/'invalid.vad'),
                                 *option.split()], capture_output=True)
        assert result.returncode != 0, option
    checks.append('OK: opcions invàlides rebutjades abans de llegir o escriure àudio.')
(root/'resultats/combinacions/comprovacions.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
