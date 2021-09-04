create database xiami_seckill CHARACTER SET=utf8 COLLATE=utf8_bin;
USE xiami_seckill;
show tables;

delete from tbl_user;

insert into tbl_user (ID,USERNAME,PASSWORD,LEVEL, BALANCE, CREATED_TS,UPDATED_TS) values(REPLACE(UUID(), '-', ''),'xyy','494576','1','100',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
insert into tbl_user (ID,USERNAME,PASSWORD,LEVEL, BALANCE, CREATED_TS,UPDATED_TS) values(REPLACE(UUID(), '-', ''),'zlj','zlj542695','1','100',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);
insert into tbl_user (ID,USERNAME,PASSWORD,LEVEL, BALANCE, CREATED_TS,UPDATED_TS) values(REPLACE(UUID(), '-', ''),'zsy','zsy','1','100',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);

commit;
