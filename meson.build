project('Práctica 2 de PAV detección de actividad vocal', 'c')

exe = 'vad'
src = ['src/main_vad.c', 'src/vad.c', 'src/pav_analysis.c']
lib = ['-lm', '-lsndfile']

entrada_docopt = files('src/vad.docopt')
generador_docopt = files('docopt_c/docopt_c.py')
python3 = find_program('python3')
cabecera_docopt = custom_target(
  'Construye vad_docopt.h',
  input: entrada_docopt,
  output: 'vad_docopt.h',
  command: [python3, generador_docopt, '@INPUT@', '-o', '@OUTPUT@'])

executable(exe, sources: [src, cabecera_docopt], link_args: lib)