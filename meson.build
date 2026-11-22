project('P2_PAV', 'C')

sndfile_dep = dependency('sndfile')
m_dep = meson.get_compiler('c').find_library('m', required : false)

inc = include_directories('src', 'docopt_c')

src = [
  'src/main_vad.c',
  'src/vad.c',
  'src/pav_analysis.c'
]

executable('vad', src, include_directories : inc, dependencies : [sndfile_dep, m_dep])
