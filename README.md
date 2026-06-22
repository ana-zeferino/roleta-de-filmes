# 🎬 Roleta de Filmes

Um app local (Mac) com uma **roleta circular flutuante** para você e seu noivo sortearem o que
assistir aos domingos. Ao sortear, mostra a **sinopse**, **onde assistir no Brasil** (+ botão para
abrir no **Stremio**) e o **trailer no YouTube**. Dá pra filtrar por **gênero**, escolher se
**séries** entram no sorteio e **editar a lista** dentro do próprio app.

Feito em **Python + pywebview** (leve, usa o navegador nativo do macOS — nada de Electron) nas
cores **azul e verde**. 💙💚

---

## 1. Pré-requisitos

- macOS com **Python 3.9+** (`python3 --version` para conferir).

## 2. Instalar

No Terminal, dentro da pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Criar a chave do TMDB (grátis, 2 min)

A sinopse, o "onde assistir" e o trailer vêm do **TMDB** (The Movie Database).

1. Crie uma conta grátis em https://www.themoviedb.org/
2. Vá em **Settings → API** e gere uma **API Key (v3 auth)**.
3. Copie o arquivo de exemplo e cole sua chave:

```bash
cp .env.example .env
```

4. Abra o `.env` e troque `cole_sua_chave_aqui` pela sua chave.

## 4. Rodar

```bash
source .venv/bin/activate   # se ainda não estiver ativo
python app.py
```

A janela circular vai abrir. 🎉

---

## Como usar

- **Girar** → sorteia um título e abre o cartão com sinopse, onde assistir e trailer.
- **Incluir séries** → ligue/desligue para incluir ou tirar todas as séries do sorteio.
- **Gêneros** → marque um ou mais para filtrar a roleta.
- **Minha lista** → adicione ou remova títulos a qualquer momento (a lista fica salva).

A lista começa a partir do seu arquivo `Sem Título.rtf` na primeira execução e depois fica salva em
`data/movies.json`.

## Gerar o app (.app) e o instalador (.dmg)

Para ter o programa de verdade (abre pelo Launchpad/Finder, sem terminal):

```bash
./build_app.sh
```

Isso gera:
- `dist/Roleta de Filmes.app` — o aplicativo
- `Roleta de Filmes.dmg` — o instalador

**Instalar:** abra o `.dmg` e arraste o ícone **Roleta de Filmes** para a pasta **Applications**.

> ⚠️ Como o app não é assinado por um certificado pago da Apple, na **primeira vez** o macOS pode
> dizer que "não pode verificar o desenvolvedor". Basta **clicar com o botão direito no app →
> Abrir → Abrir**. Depois disso ele abre normalmente com dois cliques.

Seus dados (lista de filmes) ficam salvos em
`~/Library/Application Support/Roleta de Filmes/`, então atualizar o app não apaga sua lista.

## Windows (.exe)

O `.exe` é gerado automaticamente pelo GitHub Actions (workflow `build-windows.yml`) e fica
anexado na [Release](https://github.com/ana-zeferino/roleta-de-filmes/releases). Baixe o
`Roleta-de-Filmes-Windows.exe` e dê dois cliques.

Como o `.exe` é distribuído **sem a chave do TMDB** (por segurança), configure a chave assim:

1. Abra o Explorador de Arquivos e cole na barra de endereço: `%APPDATA%\Roleta de Filmes`
   (se a pasta não existir, abra o app uma vez que ela é criada).
2. Crie ali um arquivo de texto chamado **`.env`** (exatamente assim, com o ponto na frente).
3. Coloque dentro a linha: `TMDB_API_KEY=sua_chave_aqui`
4. Salve e reabra o app.

> O Windows pode mostrar um aviso do **SmartScreen** ("Windows protegeu o computador") por o app
> não ser assinado. Clique em **Mais informações → Executar assim mesmo**.

## Dicas / problemas comuns

- **"TMDB_API_KEY não configurada"** → confira se você criou o `.env` e colou a chave.
- **Título sem sinopse / gênero errado** → o TMDB pode errar em títulos com erro de digitação. Use o
  painel **Minha lista** para remover e adicionar de novo com o nome correto.
- **Não achou o trailer** → nem todo título tem trailer cadastrado no TMDB; o botão fica desabilitado.
