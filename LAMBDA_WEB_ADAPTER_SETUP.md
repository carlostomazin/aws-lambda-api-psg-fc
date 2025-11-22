# AWS Lambda Web Adapter - Guia de Uso Correto

## O que é AWS Lambda Web Adapter?

O **AWS Lambda Web Adapter** é um layer que permite executar aplicações web convencionais (como FastAPI, Flask, Express) em AWS Lambda, convertendo eventos HTTP em requisições HTTP padrão que sua aplicação entende.

## Como funciona?

```
Request HTTP → Lambda Web Adapter → HTTP padrão → sua aplicação (FastAPI)
```

## Configuração Correta

### 1. **Layer no Lambda**
```terraform
layers = [
  "arn:aws:lambda:${data.aws_region.current.region}:753240598075:layer:LambdaAdapterLayerArm64:25"
]
```
- Use `LambdaAdapterLayerX86_64:25` para arquitetura x86_64
- Use `LambdaAdapterLayerArm64:25` para arquitetura arm64 (mais barato)

### 2. **Variáveis de Ambiente**
```terraform
environment {
  variables = {
    "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap"
    "PORT": 8000
  }
}
```

**Significado:**
- `AWS_LAMBDA_EXEC_WRAPPER`: Aponta para o bootstrap do adapter
- `PORT`: A porta onde sua aplicação rodará (qualquer porta > 1024)

### 3. **Handler**
```terraform
handler = "main.handler"
runtime = "python3.13"
```

**Importante:** O handler NÃO é `run.sh`, é um módulo Python.

### 4. **main.py**
```python
from fastapi import FastAPI

app = FastAPI()

# suas rotas aqui...

# Handler para Lambda
handler = app  # Exportar a instância do FastAPI
```

**Não precisa de função `lambda_handler` complexa!** O Web Adapter cuida disso automaticamente.

### 5. **run.sh**
```bash
#!/bin/bash
exec python -m uvicorn --port=$PORT main:app
```

**Este arquivo inicia sua aplicação FastAPI quando Lambda executar.**

### 6. **requirements.txt**
```
emoji
supabase
python-dotenv
fastapi
uvicorn[standard]  # Importante! Precisa de uvicorn
```

## Fluxo de Execução no Lambda

1. Lambda inicia → `AWS_LAMBDA_EXEC_WRAPPER` aponta para `/opt/bootstrap`
2. `/opt/bootstrap` (do layer) executa `run.sh`
3. `run.sh` inicia: `python -m uvicorn --port=8000 main:app`
4. FastAPI sobe na porta 8000
5. Web Adapter mapeia requisições HTTP para FastAPI
6. Respostas voltam como HTTP 200/201/etc

## Checklist de Verificação

- ✅ Layer adicionado ao Lambda
- ✅ `AWS_LAMBDA_EXEC_WRAPPER` = "/opt/bootstrap"
- ✅ `PORT` definida
- ✅ Handler = "main.handler" (não run.sh)
- ✅ `handler = app` exportado em main.py
- ✅ `run.sh` com permissão de execução (755)
- ✅ Uvicorn no requirements.txt
- ✅ FastAPI importado e `app` criado

## Deployment

```bash
zip -r function.zip app/
# Fazer upload: dist/function.zip
```

## Testando Localmente

```bash
export PORT=8000
export SUPABASE_URL="..."
export SUPABASE_KEY="..."
uvicorn main:app --port 8000
```

## Referências

- [AWS Lambda Web Adapter](https://github.com/aws/aws-lambda-web-adapter)
- [FastAPI com Lambda](https://docs.aws.amazon.com/pt_br/lambda/latest/dg/urls-configuration.html)
