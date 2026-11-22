"""Començo amb valors normals i vaig reduint el pas quan ja no milloro."""
import math
from cerca_adaptativa import CENTER as OLD_CENTER, INITIAL_STEP as OLD_STEP, MIN_STEP as OLD_MIN, LIMITS as OLD_LIMITS

# Blocs de 10 ms, marge en dB, log10(alfa) i diferència entre llindars.
CENTER = OLD_CENTER + (4., 55.)
INITIAL_STEP = OLD_STEP + (2., 10.)
MIN_STEP = OLD_MIN + (.1, .5)
LIMITS = OLD_LIMITS + ((1., 15.), (30., 80.))
MAX_SWEEPS = 90


def search(methods, additions, frame_ms, evaluate):
    """Faig tres inicis genèrics. Cap llegeix els guanyadors de proves anteriors."""
    quantum = frame_ms/10.0
    minimum = list(MIN_STEP)
    for index in (0,1,2,9): minimum[index] = quantum
    active = [0, 3]
    active += [index for index, enabled in [(1, methods[0]), (2, methods[1]),
                                           (4, methods[2]), (5, methods[3])] if enabled]
    if methods[8]: active += [6, 7]
    if methods[9]: active += [8, 9]
    if methods[10] and methods[2]: active += [10]
    if additions[0]: active += [11]
    if additions[1]: active += [12]
    active.sort()
    trace, finalists = [], []

    def normalize(point):
        point = list(point)
        for index, (low, high) in enumerate(LIMITS):
            point[index] = min(high, max(low, point[index]))
            if index in (0,1,2,9):
                low_tick = max(quantum, math.ceil(low/quantum)*quantum)
                high_tick = max(low_tick, math.floor(high/quantum)*quantum)
                point[index] = min(high_tick, max(low_tick, round(point[index]/quantum)*quantum))
            else:
                point[index] = round(point[index], 8)
        return tuple(point)

    def config(point):
        init, voice, silence, margin, log_alpha, gap, zcr, discount, boost, wait, update, down, voice_range = normalize(point)
        if not methods[0]: voice = 1
        if not methods[1]: silence = 1
        alpha = float(f'{10**log_alpha:.8g}') if methods[2] else 0.
        gap = gap if methods[3] else 0.
        if not methods[8]: zcr, discount = 3000., 2.
        if not methods[9]: boost, wait = 3., 25
        if not methods[10] or not methods[2]: update = 2.
        # Els temps de la cerca són blocs nominals de 10 ms.
        duration = lambda blocks: max(1, int(round(blocks*10/frame_ms)))
        init = max(2 if methods[4] else 1, duration(init))
        voice = duration(voice) if methods[0] else 1
        silence = duration(silence) if methods[1] else 1
        wait = max(voice, duration(wait))
        alpha = float(f'{1-(1-alpha)**(frame_ms/10):.8g}') if methods[2] else 0.
        if not additions[0]: down = 4.
        if not additions[1]: voice_range = 55.
        return (init, voice, silence, margin, alpha, gap, *methods[4:], zcr, discount, boost, wait, update,
                *additions, down, voice_range, frame_ms)

    def valid(point):
        c = config(point)
        return c[5] < c[3] and (not methods[8] or c[14] < c[3]) and (not methods[9] or c[16] >= c[1])

    for start, offset in enumerate((-1, 0, 1)):
        point = normalize([value+offset*step for value, step in zip(CENTER, INITIAL_STEP)])
        steps = list(INITIAL_STEP)
        for index in (0,1,2,9):
            steps[index] = max(quantum, math.ceil(steps[index]/quantum)*quantum)
        for sweep in range(MAX_SWEEPS):
            before = point
            for dimension in active:
                candidates = [point]
                for sign in (-1, 1):
                    neighbor = list(point)
                    neighbor[dimension] += sign*steps[dimension]
                    neighbor = normalize(neighbor)
                    if valid(neighbor): candidates.append(neighbor)
                point = max(candidates, key=lambda p: evaluate(config(p))[0])
            # Si moure marge o alfa sols no ajuda, també miro les quatre cantonades.
            if methods[2]:
                candidates = [point]
                for margin_sign in (-1, 1):
                    for alpha_sign in (-1, 1):
                        neighbor = list(point)
                        neighbor[3] += margin_sign*steps[3]
                        neighbor[4] += alpha_sign*steps[4]
                        neighbor = normalize(neighbor)
                        if valid(neighbor): candidates.append(neighbor)
                point = max(candidates, key=lambda p: evaluate(config(p))[0])
            improved = evaluate(config(point))[0] > evaluate(config(before))[0]
            finished = not improved and all(steps[i] <= minimum[i] for i in active)
            trace.append({'inici_cerca': start+1, 'volta': sweep+1,
                          'config': config(point), 'total': evaluate(config(point))[0],
                          'passos': tuple(steps),
                          'accio': 'moure' if improved else ('aturar' if finished else 'reduir_pas')})
            if finished:
                break
            if not improved:
                for dimension in active:
                    step = steps[dimension]/2
                    if dimension in (0, 1, 2, 9): step = math.ceil(step/quantum)*quantum
                    steps[dimension] = max(minimum[dimension], step)
        finalists.append((point, finished))
    best, _ = max(finalists, key=lambda pair: evaluate(config(pair[0]))[0])
    return config(best), trace, sum(not finished for _, finished in finalists)
