"""Començo amb valors normals i vaig reduint el pas quan ja no milloro."""
import math

# Blocs de 10 ms, marge en dB, log10(alfa) i diferència entre llindars.
CENTER = (10, 5, 15, 6., -2., 1., 3000., 2., 3., 25, 2.)
INITIAL_STEP = (5, 3, 5, 2., .5, .5, 1000., 1., 1., 10, 1.)
MIN_STEP = (1, 1, 1, .01, .005, .01, 25., .02, .01, 1, .01)
LIMITS = ((2, 40), (2, 20), (2, 50), (2., 14.), (-4., -1.), (.01, 4.), (500., 6000.), (.1, 6.), (.1, 8.), (2, 60), (0., 6.))
MAX_SWEEPS = 60


def search(methods, evaluate):
    """Faig tres inicis genèrics. Cap llegeix els guanyadors de proves anteriors."""
    active = [0, 3]
    active += [index for index, enabled in [(1, methods[0]), (2, methods[1]),
                                           (4, methods[2]), (5, methods[3])] if enabled]
    if methods[8]: active += [6, 7]
    if methods[9]: active += [8, 9]
    if methods[10] and methods[2]: active += [10]
    active.sort()
    trace, finalists = [], []

    def normalize(point):
        point = list(point)
        for index, (low, high) in enumerate(LIMITS):
            point[index] = min(high, max(low, point[index]))
            point[index] = int(round(point[index])) if index in (0, 1, 2, 9) else round(point[index], 8)
        return tuple(point)

    def config(point):
        init, voice, silence, margin, log_alpha, gap, zcr, discount, boost, wait, update = normalize(point)
        if not methods[0]: voice = 1
        if not methods[1]: silence = 1
        alpha = float(f'{10**log_alpha:.8g}') if methods[2] else 0.
        gap = gap if methods[3] else 0.
        if not methods[8]: zcr, discount = 3000., 2.
        if not methods[9]: boost, wait = 3., 25
        if not methods[10] or not methods[2]: update = 2.
        return (init, voice, silence, margin, alpha, gap, *methods[4:], zcr, discount, boost, wait, update)

    def valid(point):
        c = config(point)
        return c[5] < c[3] and (not methods[8] or c[14] < c[3]) and (not methods[9] or c[16] >= c[1])

    for start, offset in enumerate((-1, 0, 1)):
        point = normalize([value+offset*step for value, step in zip(CENTER, INITIAL_STEP)])
        steps = list(INITIAL_STEP)
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
            finished = not improved and all(steps[i] <= MIN_STEP[i] for i in active)
            trace.append({'inici_cerca': start+1, 'volta': sweep+1,
                          'config': config(point), 'total': evaluate(config(point))[0],
                          'passos': tuple(steps),
                          'accio': 'moure' if improved else ('aturar' if finished else 'reduir_pas')})
            if finished:
                break
            if not improved:
                for dimension in active:
                    step = steps[dimension]/2
                    if dimension in (0, 1, 2, 9): step = math.ceil(step)
                    steps[dimension] = max(MIN_STEP[dimension], step)
        finalists.append((point, finished))
    best, _ = max(finalists, key=lambda pair: evaluate(config(pair[0]))[0])
    return config(best), trace, sum(not finished for _, finished in finalists)
