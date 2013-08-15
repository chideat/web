create database test;

create table test
(
id int(11) not null auto_increment,
path char(255) not null,
category char(50) not null,
state tinyint default 0,
primary key(id)
)


create table thumb
(
id int(11) not null auto_increament,
path char(255) not null,
category char(50) not null,
state tinyint default 0,
primary key(id)
)
