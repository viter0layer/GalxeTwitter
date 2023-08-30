# GalxeTwitter
Между фунциами котролируете с переменной `mode` в `data/config.py`

1. функция `verify_on_galxe` (Requests + Selenium) -
    1. проходит авторизацию на сайте Galxe
    2. Создает username с рандомным ником
    3. Запрашивает GID этого юзера от Galxe
    4. Постит твит с текстом для верификации на Galxe с помощью Selenium
    5. Привязывает твиттер на Galxe

2. функция `complete_social_tasks` (Requests):
   1. проходит все соц задания которые указаны в config - пока что там соц задание полихедры (можно изменить на другие проекты - надо найти ID задании в линке )
   ![img.png](img.png)
   2. если вы добавляете новые задачи то их надо тоже добавить в `data/consts.py`
   2. работает асинхронно, в файле config можете указать кол потоков (`wallets_in_batch`)

3. функция `claim_points` (Requests):
   1. работает асинхронно и клеймит задание которые указаны в `data/tasks_for_claim`
   2. то что не уделось заклеймить будет написанно в таблице
   3. **тут приватники не нужны - только адресса в файл `data/keys.txt`**

## Запуск
1. Устанавливаем Python 3.10.
2. Открываем терминал, переходим в папку с файлами и пишем команду `pip install -r requirements.txt`.
3. Открываем файл `data/config.py` с помощью любого текстового редактора и подбиваем настройки рандомизации. Все пояснения по настройкам описаны в комментариях в самом файле.
4. Открываем файл `data/profile_ids.py` с помощью любого текстового редактора и забиваем свои профиля (каждая строка 1 профиль)
5. Открываем файл `data/twitter_handles.txt` и забиваем туда свои Twitter Username, так, чтоб они соответствовали аккаунтам, вбитым в файл `data/profile_ids.py`.
6. Открываем файл `data/proxies` и забиваем туда proxy в формате user:pass@ip:port (без `http`)
7. Открываем файл `data/keys` и забиваем туда приватники акков которые хотите чтоб привязались к Galxe
8. Открываем файл `data/tasks_for_claim` и забиваем туда линки для клейма задач
9. Открываем терминале, находясь в папке проекта, вписываем команду `python3 main.py` и жмем ENTER.


## в файле "data/config" нужно поменять значение W на свое (инструкция ниже)
![image](https://user-images.githubusercontent.com/117441696/210056890-bc69281a-a7aa-4681-9722-4d65fd07c957.png)
