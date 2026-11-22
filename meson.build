
project('Práctica 2 de PAV - detección de actividad vocal', 'c')

exe = 'vad'
src = ['src/main_vad.c', 'src/vad.c','src/pav_analysis.c']

sndfile = dependency('sndfile', required: true)
math = meson.get_compiler('c').find_library('m', required: false)

executable(exe, sources: src, dependencies: [sndfile, math])

