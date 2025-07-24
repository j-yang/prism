**************************************************************************;
* Program name      : logcheck_tlf.sas
*
* Program path      : root/cdar/d169/d169cc00001/ar/bdr2/tlf/dev/program
*
* Type              : SAS program
*
* Purpose           : Scanning TLF dataset logs
*
* Author            : Damian Kruszewski
*
* Date created      : 03 Sep 2021
*
* Input datasets    : N/A
*
* Macros used       : %setup, %localsetup, %logcheck
*
* Output files      : N/A
*
* Usage notes       :
* 
**************************************************************************;
* Revision history  :
*
* Date        Author      Ref               Revision
*                    <<num of commit ver.>> <<details>>
**************************************************************************;




%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/%scan(&_exec_programpath.,8,/)/macro/localsetup.sas);

%localsetup;

*options mprint mlogic symbolgen;
%logcheck(fnamep=logcheck_&delivery_namex._%scan(&_exec_programpath.,8,/), 
          list=full,
          logdir=&studydir./&delivery_namex./%scan(&_exec_programpath.,8,/)/log, 
          outdir=&studydir./&delivery_namex./%scan(&_exec_programpath.,8,/)/output,
          star_check=1);
