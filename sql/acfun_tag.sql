CREATE TABLE if not exists `acfun_tag` (
  `tagId` varchar(11) UNIQUE,
  `tagName` varchar(45) DEFAULT NULL,
  `refCount` int(11) DEFAULT NULL,
  PRIMARY KEY (`tagId`)
)DEFAULT CHAR SET utf8;