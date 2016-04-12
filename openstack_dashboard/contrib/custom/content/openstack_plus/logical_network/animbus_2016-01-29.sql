# ************************************************************
# Sequel Pro SQL dump
# Version 4499
#
# http://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 192.168.203.135 (MySQL 5.5.40-MariaDB-wsrep)
# Database: animbus
# Generation Time: 2016-01-29 08:36:08 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table logical_topology
# ------------------------------------------------------------

DROP TABLE IF EXISTS `logical_topology`;

CREATE TABLE `logical_topology` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted` tinyint(1) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `link` text,
  `hulls` varchar(255) DEFAULT NULL,
  `extra` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `logical_topology` WRITE;
/*!40000 ALTER TABLE `logical_topology` DISABLE KEYS */;

INSERT INTO `logical_topology` (`created_at`, `updated_at`, `deleted_at`, `deleted`, `id`, `name`, `type`, `link`, `hulls`, `extra`)
VALUES
	(NULL,NULL,NULL,0,1,'Controller1','hulls','null',NULL,'null'),
	(NULL,NULL,NULL,NULL,2,'Controller2','hulls','null',NULL,'null'),
	(NULL,NULL,NULL,NULL,3,'Computer1','computers','null','6','null'),
	(NULL,NULL,NULL,NULL,4,'Mysql1','databases','null','1','null'),
	(NULL,NULL,NULL,NULL,5,'Haproxy1','haproxys','{\"3\": \"5\",\"4\": \"5\",\"7\":\"5\", \"8\":\"5\"}','1','null'),
	(NULL,NULL,NULL,NULL,6,'Zone1','hulls','null',NULL,'null'),
	(NULL,NULL,NULL,NULL,7,'RabbitMQ1','mqs','null','1','null'),
	(NULL,NULL,NULL,NULL,8,'Keystone1','keystones','null','1','null'),
	(NULL,NULL,NULL,NULL,10,'Computer2','computers','null','6','null'),
	(NULL,NULL,NULL,NULL,12,'Mysql2','databases','null','2','null'),
	(NULL,NULL,NULL,NULL,13,'RabbitMQ2','mqs','null','2','null'),
	(NULL,NULL,NULL,NULL,14,'Keystone2','keystones','null','2','null'),
	(NULL,NULL,NULL,NULL,15,'Haproxy2','haproxys','{\"10\": \"15\",\"12\": \"15\",\"13\":\"15\", \"14\":\"15\"}','2','null');

/*!40000 ALTER TABLE `logical_topology` ENABLE KEYS */;
UNLOCK TABLES;



/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
