Простенький веб-сервер, поднимаемый рядом с бд, управляющий репликацией и промоутом. 

#### Api запросы:

* `/status` - возвращает информацию о статусе ноды (режим, в котором запущена, мастер или реплика, приоритет)
* `/is_available?node_ip=<ip>` - дергает предыдущую ручку для указаного адреса. Для выполнения функционала арбитра
* `/node_info` - возвращает вывод `pg_controldata`, чтобы можно было убедиться в промоуте

#### Как работать

Склонировать репозиторий: `git clone https://github.com/mikhailantoshkin/replicant.git`

Собрать образы docker: `docker-compose build`

Запустить: `docker-compose up -d`

Дернуть мастера `curl http://localhost/status` и увидеть, что с ним все норм:
```
{
   "mode": "node",
   "master": true,
   "priority": "0",
   "nodes": {
      "arbiter": "AVAILABLE",
      "replica": "AVAILABLE"
   }

```

Спросить у мастера и реплики `/node_info` и убедиться, что для мастера
```.env
Database cluster state:               in production
```
для реплики
```
Database cluster state:               in archive recovery
```
Так же можно дернуть арбитра(порт `8070`) и реплику (порт `8080`)

По готовности положить мастера: `docker stop master`

Через несколько секунд реплика начнет отвечать, что она теперь мастер

```
{
   "mode": "node",
   "master": true,
   "priority": "1",
   "nodes": {
      "arbiter": "AVAILABLE",
      "master": "UNAVAILABLE"
   }

```

Дернуть `/node_info` у реплики и посмотреть, что `Database cluster state` теперь `in production`

При желании можно провалиться в контейнер `docker exec -ti replica bash` и посмотреть что же там в базе 
```.env
psql -U hamed hamed

psql (12.3 (Debian 12.3-1.pgdg100+1))
Type "help" for help.

hamed=# \dt
       List of relations
 Schema | Name  | Type  | Owner 
--------+-------+-------+-------
 public | users | table | hamed
(1 row)

hamed=# select * from users;
 id | name |    dob     
----+------+------------
  1 | Bob  | 1984-03-01
(1 row)

```


