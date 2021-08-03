create database xiami_seckill CHARACTER SET=utf8 COLLATE=utf8_bin;
USE xiami_seckill;
show tables;

delete from tbl_user;

insert into tbl_user (ID,USERNAME,PASSWORD,MOBILE,PAYMENT_PWD,LEVEL, BALANCE, CREATED_TS,UPDATED_TS) values(REPLACE(UUID(), '-', ''),'admin123','admin123','','','1','100',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);

commit;