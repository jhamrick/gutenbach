/*
 * $Id: voldaemon.c,v 1.1 2008-09-27 08:49:10 root Exp $
 * $Source: /tmp/tmp.UFBNno9997/RCS/voldaemon.c,v $
 */

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <errno.h>
#include <assert.h>
#include <netinet/in.h>


#define LISTEN_PORT 8930
#define MULTI_PORT 8931
#define MULTI_ADDR "224.0.1.20"

/* Block queries from off this subnet net 18.*/
#define OUR_SUBNET      187

typedef struct volmessage{
  char A;
  char request;
  char value;
  unsigned char ip_3;
  unsigned char ip_2;
  unsigned char ip_1;
  unsigned char ip_0;
  char ZE;
} volmessage;

#define MESSAGE_SIZE (sizeof(volmessage))

/* The client makes requests using the following packets.  Responses
   to queries and status reports from the server follow the same
   pattern

  Request/Response

  'AVxiiiiZ'     Volume
  'AMxiiiiZ'     Mute
  'AQQiiiiZ'     Query 

  Response Only
  'AVeiiiiE'     Volume Set Error 
  'AMeiiiiE'     Mute Set Error 
  'AEeiiiiE'     Unknown error 

   e=1  Permission denied (invalid IP)
   e=2  Invalid request (Bad Packet)
   
*/

void message(char *m){
  write(STDERR_FILENO,m,strlen(m));
}

void abortm(char *m){
  message(m);
  message("Errno = ");
  message(strerror(errno));
  message("\n");
  exit(1);
}

struct in_addr multiaddr={0};

int multicast(volmessage *m){
  static int sockfd=-1;
  static struct sockaddr_in dest;
  int destlen=sizeof(dest);

  if(sockfd==-1)
    if((sockfd=socket(AF_INET,SOCK_DGRAM,0))<0)
      abortm("Could not open multicast socket\n");

  if(multiaddr.s_addr==0)
    multiaddr.s_addr = inet_addr(MULTI_ADDR);
      /*inet_aton(MULTI_ADDR,&multiaddr);*/

  memset(&dest,0,sizeof(dest));
  dest.sin_family=AF_INET;
  dest.sin_addr.s_addr=multiaddr.s_addr;
  dest.sin_port=htons(MULTI_PORT);

  if(sendto(sockfd,m,MESSAGE_SIZE,0,(struct sockaddr *)&dest,destlen)<0){
    message("Multicast send error\n");
    return(1);
  }
  return(0);
}

int sockfd=-1,volfd;
static struct sockaddr_in me,you;
static int youlen=sizeof(you);
struct in_addr multiaddr;

int opensock(){
  if((sockfd=socket(AF_INET,SOCK_DGRAM,0))<0)
    abortm("Could not open listen socket\n");

  memset(&me,0,sizeof(me));
  me.sin_family=AF_INET;
  me.sin_addr.s_addr=htonl(INADDR_ANY);
  me.sin_port=htons(LISTEN_PORT);

  if(bind(sockfd,(struct sockaddr *)&me,sizeof(me))<0)
    abortm("Could not bind to listen port\n");

  listen(sockfd,5);
  return(sockfd);
}

/*  -1 blocks
    0  nonblocking
    +n timeout 
*/

int
fetch (int usec, volmessage *m) {
  fd_set fdset;
  int retval;
  struct timeval tv;
  if(sockfd==-1)
    opensock();

  FD_ZERO(&fdset);
  FD_SET(sockfd, &fdset);

  tv.tv_sec = 0;
  tv.tv_usec = usec;
  retval = select(sockfd+1,
		  &fdset, NULL, NULL,
		  ((usec == -1) ? NULL : &tv));
  if (retval == 1) {
    /* Select got us a single descriptor to play with, as we
     * expected. Pull a message from it. */
    int youlen = sizeof(you);
    retval = recvfrom(sockfd,
		      m, MESSAGE_SIZE,
		      0,
		      (struct sockaddr *)&you, &youlen);
    if(retval < MESSAGE_SIZE || m->A != 'A' || m->ZE != 'Z') {
      message("Packet receive error\n");
      return(0);
    } else {
      return(1);
    }
  } else {
    if (retval == 0) {
      /* This means the timeout finished. */
    } else if (retval == -1) {
      fprintf(stderr, "Select error. errno = %d (%s).\n",
	      errno, strerror(errno));
    } else {
      fprintf(stderr, "Select returned unexpected value %d.\n", retval);
    }
    /* Whatever error we get, we just return 0. */
    return(0);
  }
}


int
reply (volmessage *m) {
  int retval;
  assert(sockfd != -1);
  
  retval = sendto(sockfd,
		  m, MESSAGE_SIZE,
		  0,
		  (struct sockaddr *)&you, youlen);
  if(retval < 0){
    message("Reply error\n");
    return(1);
  }
  return(0);
}
  
int vol_iterate(int newval){
  static int val=0;
  char command[100];
  

  if (val==newval)
    return(0);

  if (val<newval) {
    val+=8;
    if(val>newval)
      val=newval;
  } else {
    val-=8;
    if(val<newval)
      val=newval;
  }
  sprintf(command,"/usr/bin/aumix -v %d",val);
  fprintf(stderr,"Setting volume to %d\n",val);
  system(command);
  return(1);
}

int main(){
  unsigned char volume=32,mute=0,ip_3=0,ip_2=0,ip_1=0,ip_0=0;
  int messagestatus=1,volstatus=1;
  volmessage m;

  system("/usr/bin/aumix -v 0");
  system("/usr/bin/aumix -i 100");
  system("/usr/bin/aumix -l 100");

  message("\nSIPB volume daemon running\n");

  /* We want to process messages quickly, then get to the business of
     controlling ther hardware when no messages are in the queue. 
     The select on the message fetch also does our timing for volume
     iteration */

  while(1){
    if(messagestatus==1)
      /* Messages likely pending.  Process quickly */
      messagestatus=fetch(0,&m);
    else
      if(volstatus==1){
	/* No messages, but volume to be updated */
	messagestatus=fetch(50,&m);
	if(messagestatus==0)volstatus=vol_iterate(mute?0:volume);
      }else{
	/* Steady state.  Wait (almost) forever until a message */
	m.ip_0=ip_0;
	m.ip_1=ip_1;
	m.ip_2=ip_2;
	m.ip_3=ip_3;
	m.A='A';
	m.request='V';
	m.value=volume;
	m.ZE='Z';
    	multicast(&m);
	m.A='A';
	m.request='M';
	m.value=mute;
	m.ZE='Z';
    	multicast(&m);
	messagestatus=fetch(400000,&m);
      }

    if(messagestatus){
      int error=0;
      m.ip_3=(ntohl(you.sin_addr.s_addr)>>24)&0xff;
      m.ip_2=(ntohl(you.sin_addr.s_addr)>>16)&0xff;
      m.ip_1=(ntohl(you.sin_addr.s_addr)>>8)&0xff;
      m.ip_0=ntohl(you.sin_addr.s_addr)&0xff;

      if(m.ip_3!=18 || m.ip_2!=OUR_SUBNET){
	error=1;
      }

      switch(m.request){
      case 'V':
	if(error){
	  m.value=error;
	  m.ZE='E';
	  reply(&m);
	  message("Request from off subnet rejected\n");
	}else{
	  ip_0=m.ip_0;
	  ip_1=m.ip_1;
	  ip_2=m.ip_2;
	  ip_3=m.ip_3;
	  volume=m.value;
	  reply(&m);
	  multicast(&m);
	  volstatus=1;
	}
	break;
      case 'M':
	if(error){
	  m.value=error;
	  m.ZE='E';
	  reply(&m);	  
	  message("Request from off subnet rejected\n");
	}else{
	  ip_0=m.ip_0;
	  ip_1=m.ip_1;
	  ip_2=m.ip_2;
	  ip_3=m.ip_3;
	  mute=(m.value?1:0);
	  m.value=mute;
	  reply(&m);
	  multicast(&m);
	  volstatus=1;
	}
	break;
      case 'Q':
	m.ip_0=ip_0;
	m.ip_1=ip_1;
	m.ip_2=ip_2;
	m.ip_3=ip_3;
	m.request='V';
	m.value=volume;
	reply(&m);
	m.request='M';
	m.value=mute;
	reply(&m);
	break;
      default:
	reply((volmessage *)"AE20000E");
	break;
      }
    }
  }
}
