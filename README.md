# Automacao de Glosas Amil

Aplicacao desktop em Python para automatizar preenchimento de glosas no portal da Amil com base em planilha (`.xlsx` ou `.csv`).

## Requisitos

- Python 3.11+
- Google Chrome instalado
- Dependencias Python:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Formato da planilha

Colunas obrigatorias (nomes exatos):

- `numero_guia`
- `senha`
- `valor_glosa`
- `justificativa`

Chave de busca utilizada: `numero_guia + senha`.

Tambem aceita nomenclatura do consolidado Amil, por exemplo:
- `Número da Guia no Prestador` -> `numero_guia`
- `Senha` -> `senha`
- `Valor Glosa (R$)` -> `valor_glosa`
- `Justificativa para recurso.` -> `justificativa`
- `Código da Glosa da Guia` -> `codigo_glosa` (opcional, usado em regras especiais)

## Como executar

```bash
python main.py
```

Fluxo recomendado:

1. Clique em `Abrir Chrome (Depuracao)`.
2. O Chrome abre diretamente em `https://credenciado.amil.com.br/`.
3. Navegue manualmente ate o lote que sera recursado.
4. Selecione a planilha na GUI.
5. Clique em `Iniciar`.

## Comportamento de erro

- Se a chave `numero_guia|senha` nao existir na planilha, o sistema marca `Erro` e entra em `PAUSADO`.
- Nessa pausa, voce pode:
  - `Retomar` (retentar a mesma guia),
  - `Pular Guia Atual`,
  - `Encerrar`.
- Sempre que ocorre erro (nao encontrado ou falha de preenchimento), o sistema salva screenshot em `reports/screenshots/`.
- Regra especial: quando `codigo_glosa` for `3052`, o sistema **nao preenche valor** e usa `//*[@id='justificativa_guia']` para justificar.

## Relatorio final

- Ao finalizar (`FINALIZADO` ou `PARADO`), o app exporta um CSV em `reports/` com o historico das guias processadas.
- O caminho do arquivo aparece no log e no alerta final.

## Seletores do portal

Os seletores padrao estao em `app/config.py` e ja configurados para:
- `//*[@id='num_guia_operadora_recurso']`
- `//*[@id='senha']`
- `//*[@id='guia_final']`
- `//*[@id='valor_recursado']`
- `//*[@id='justificativa_prestador_procedimento']`
- `//*[@id='btn_guia_posterior']`

`lote` e `protocolo` sao opcionais por padrao.  
Para customizar sem alterar codigo:

1. Copie `settings.example.json` para `settings.json`.
2. Ajuste `portal_url` (se necessario) e o bloco `selectors` para a estrutura real da pagina.
