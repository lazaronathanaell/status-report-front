# Benchmark autônomo da pipeline Ollama

Este diretório executa preprocessamento, extração, estruturação, avaliação por
ground truth, validação cruzada e medição contínua de recursos. Não inicia nem
importa Kafka, Celery, API, frontend ou PostgreSQL.

## Compatibilidade documental

- PDF híbrido: limiar de 5% de área de texto e OCR Tesseract português a 600 DPI.
- DOE: contexto reduzido ao redor do nome cadastrado.
- Diploma: o modo padrão preserva a extração original. O modo experimental
  `DIPLOMA_PREPROCESS_MODE=benchmark_slms` força OCR na primeira página, combina
  texto nativo + OCR e recorta servidor/validação eletrônica.
- ASJUR: prompts inicial e final executados sobre os recortes da task original.
- Repercussão: tabelas PyMuPDF e filtros específicos das páginas 1 e 2.
- Pós-processamento: schemas, limpeza de matrícula e agregação anual originais.

`GENERATION_MODE=original` usa o payload lógico da aplicação. O modo
`controlled` força JSON, temperatura e seed para comparação determinística.
No processo de validação, o modo experimental do diploma reduziu a acurácia de
20/20 para 19/20; por isso ele não é o padrão, mas permanece disponível para
ablação no artigo.

## Preparação dos processos

Coloque os PDFs completos em `raw/<NUP>.pdf`. O `index.json` incluído informa as
páginas e os metadados de cada documento.

Para preparar processos específicos:

```powershell
.\preprocess.ps1 -Process 22001135305202440,22001127982202494
```

O resultado é gravado em `data/<NUP>/`:

```text
data/<NUP>/
  pdfs/
  ground_truth/
  profile.json
```

O preprocessador corrige os problemas do script de pesquisa anterior: caminhos
divergentes, limitação à primeira pasta, intervalos invertidos e dependência da
aplicação completa. A extração/OCR é feita durante a bateria para que seu consumo
também seja medido.

## Uma execução

```powershell
.\run.ps1
```

Para trocar o modelo, copie um arquivo de `configs/`, altere `OLLAMA_MODEL` e
informe-o em `-EnvFile`.

## Matriz de modelos e processos

`matrix_runner.py` usa esta ordem deliberadamente:

```text
modelo X -> processo 1 .. processo 8
modelo Y -> processo 1 .. processo 8
modelo Z -> processo 1 .. processo 8
```

O Ollama permanece ativo. Cada modelo é baixado/verificado uma vez e executa
todos os processos antes da troca. Cada combinação possui resultados e métricas
próprios; um resumo da matriz é escrito em `results/matrices/<run_group_id>/`.

Por padrão, `remove_model_after_group=true`: depois do último processo do modelo,
a matriz executa `ollama stop` e `ollama rm` antes de baixar o próximo. Isso libera
RAM/VRAM e remove do volume os arquivos exclusivos do modelo. Camadas que sejam
compartilhadas com outro modelo podem permanecer. Use `false` para preservar o
cache e acelerar repetições futuras.

Durante os oito processos, `model_keep_alive="-1"` mantém apenas o modelo corrente
carregado para evitar recarga a cada PDF. `OLLAMA_MAX_LOADED_MODELS=1` impede dois
modelos simultâneos. Na troca, `stop` libera RAM/VRAM e `rm` recupera espaço em disco.

Edite `matrix.json` ou copie `matrix.example.json` e execute:

```powershell
.\run-matrix.ps1 -Matrix matrix.example.json -EnvFile configs/example.env
```

Antes de iniciar o Docker, a matriz valida se todos os oito diretórios, ground
truths e perfis existem. `continue_on_error=true` permite registrar uma falha e
continuar os demais processos/modelos.

## Recursos

CPU e RAM são limites reais do Docker. `GPU_DEVICE_ID` seleciona a GPU e
`GPU_VRAM_RESERVE_BYTES` reserva memória para o sistema. GPUs NVIDIA comuns não
oferecem hard cap de VRAM por container; limite rígido exige MIG/vGPU. O monitor
registra CPU, RAM, GPU, VRAM, potência e temperatura aproximadamente a cada
segundo durante cada processo.

Cada linha de `resources.csv` inclui `run_id`, `run_group_id`, modelo, processo e
índices da matriz. `resources_summary.json`, `summary.json` e o resumo agregado da
matriz repetem esses identificadores, permitindo junção sem depender do nome da
pasta.
