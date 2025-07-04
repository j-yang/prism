**************************************************************************;
* Program name      : @@program_name
*
* Program path      : root/cdar/d693/d6935c00003/ar/dr1/adam/work_val/program
*
* Type              : SAS program
*
* Purpose           : @@purpose
*
* Author            : @@author
*
* Date created      : @@date
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %vm_adam_mergesupp, %vm_adam_attrib
*
* Output files      : @@output
*
* Usage notes       :  
**************************************************************************;

%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/dev/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%let domain=%upcase(%scan(&PGMNAME,2, "_"));
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Merge supp to main domain*/
%*vm_adam_mergesupp(domain= , );


/*Step 2: Analysis dataset creation*/











/*Step 3: Assign attributes to dataset and variables*/;
%vm_adam_attrib(domain=, indsn=final, adsllib=adam, outlib=adam_qc, chklen=Y, sameTRTVar=Y, specdir= &adamspec., hasASEQ=Y);


/*Step 4: Compare with dev side ouput*/;
ods listing close;
ods listing file="&studydir./&delivery_namex./%scan(&_exec_programpath.,8,/)/output/%lowcase(&pgmname.).lst";
proc compare base=adam.&domain. comp = adam_qc.&domain. 
out=chk_&domain.  outbase outcomp outdiff outnoequal listall criteria=0.0001 warning error ;
quit;
ods listing close;

/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

