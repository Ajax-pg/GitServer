# GitServe (Projeto Pessoal)

Orientações: **! NÃO OFICIAL DO GITHUB !**   



  Essa biblioteca tem seu objetivo criar um servidor usando do Python e o GitHub, tornando uma maneira facil o desenvolvimento de servidores, ela usa de `class`, que é um objeto criado por mim, que seria uma pasta, e a `table`, que é um arquivo json dentro da class, veja abaixo como usar tal biblioteca:

## Iniciando servidos
  Para iniciar um servidor, precisamos de repositório, onde os dados estarão e um token para conectar ao repositório.
  
```python
sev = server('TOKEN', 'REPO')
```

  Se tudo deu certo, deve está aparecendo a seguinte menssagem:

```
= Note ================================================
Server initialized with:
[TIME]             [2025-06-27 16:33:33]
[SERVER]                            [ON]
[GUITHUB]                    [CONNECTED]
[REPOSITORY]                 [CONNECTED]
[TOKEN]                      [CONNECTED]
=======================================================
```

## Como criar uma class
  Para isso, devemos escrever o seguinte comando:
  
```python
minha_class = sev.create_class('NOME')
```

## Como criar uma table
  Para isso, devemos escrever o seguinte comando:
  
```python
minha_table = sev.create_table(minha_class, 'NOME')
```




