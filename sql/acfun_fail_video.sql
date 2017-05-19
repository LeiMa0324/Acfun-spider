CREATE TABLE if not exists `acfun_fail_video` (
  `id` varchar(11) UNIQUE,
  `FailReason` VARCHAR(1) NULL ,
  `status_code` int(3) NULL ,
  `type` int(1) NULL ,
  `create_time` varchar(45) NULL ,
  PRIMARY KEY (`id`)
)DEFAULT CHAR SET utf8;