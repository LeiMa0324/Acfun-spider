CREATE TABLE if not exists `acfun_video` (
  `id` varchar(11) UNIQUE,
  `uid` varchar(45) DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  ` contributeTime` varchar(45) DEFAULT NULL,
  ` description` text DEFAULT NULL,
  ` duration` int(45) DEFAULT NULL,
  ` banana` int(11) DEFAULT NULL,
  ` playnum` int(11) DEFAULT NULL,
  ` commentnum` int(11) DEFAULT NULL,
  ` bulletnum` int(11) DEFAULT NULL,
  ` favoritenum` int(11) DEFAULT NULL,
  ` tags` text DEFAULT NULL,
  PRIMARY KEY (`id`)
)DEFAULT CHAR SET utf8;