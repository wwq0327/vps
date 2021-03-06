namespace py saas 

typedef i64 Ip 


struct Vps {
   1 : i64 id                        ,
   2 : optional Ip ipv4              ,
   3 : optional Ip ipv4_netmask      ,
   4 : optional Ip ipv4_gateway      ,
   5 : string password               ,
   6 : i64 os                        ,                       //os的id会软连接到真实的os镜像
   7 : i16 hd                        ,                       //单位G
   8 : i64 ram                       ,                       //单位M
   9 : i16 cpu                       ,                       //几个core
  10 : i64 host_id                   ,                       //如pc1.42qu.us
/*
VPS_STATE_RM = 0
VPS_STATE_PAY = 10
VPS_STATE_RUN = 15
VPS_STATE_CLOSE = 20

VPS_STATE2CN = {
    VPS_STATE_RM  : '已删除' ,
    VPS_STATE_RUN : '运行中' ,
    VPS_STATE_CLOSE : '被关闭' ,
    VPS_STATE_PAY : '未开通' ,
}
*/
  11 : i16 state                     ,
  12 : optional Ip ipv4_inter        ,                       //内网IP
  13 : optional i64 bandwidth        ,                       //带宽 单位 Mbps, 0 或 None 表示不限制
  14 : optional i32 qos              ,                       //带宽优先级 0 为默认值 , 1 为高优先级
}

struct NetFlow {
	1: i64 vps_id					,
	2: i64 rx						,
	3: i64 tx						,
}

enum Cmd{
  NONE        = 0,
  OPEN        = 1,
  CLOSE       = 2,
  REBOOT      = 3,
  RM          = 4,
  BANDWIDTH   = 5, //调整带宽
  OS          = 6, //更换操作系统
}


typedef i64 VpsId 
typedef i64 Id

service VPS {

   Id    todo            ( 1:i64  host_id , 2:Cmd cmd),
   void  done            ( 1:i64  host_id , 2:Cmd cmd, 3:Id id, 4:i32 state=0, 5:string message=''), 

   Vps   vps             ( 1:i64 vps_id   ),
   void  netflow_save    ( 1:i64 host_id, 2:list<NetFlow> netflow, 3:i64 timestamp),

   void  plot            ( 1:i64 cid, 2:i64 rid, 3:i64 value ),

   string   sms          ( 1:list<string>  number_list, 2:string txt),
   void  host_refresh    ( 1:i64 host_id , 2:i16 hd_remain, 3:i64 ram_remain),
}



