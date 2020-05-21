Простенький веб-сервер, поднимаемый рядом с бд, управляющий репликацией и промоутом. 

Api запросы:

* `/status` - возвращает информацию о статусе ноды (режим, в котором запущена, мастер или реплика, приоритет)
* `/is_available?node_ip=<ip>` - дергает предыдущую ручку для указаного адреса. Для выполнения функционала арбитра
* `/node_info` - возвращает вывод `pg_controldata`, чтобы можно было убедиться в промоуте