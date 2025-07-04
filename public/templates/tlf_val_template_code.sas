*************************************************************************;
* Program name      : @@program_name
*
* Program path      : root/cdar/d693/d6935c00003/ar/dr1/tlf/work_val/program
*
* Type              : SAS program
*
* Purpose           : @@purpose
*
* Author            : @@author
*
* Date created      : @@date
*
* Input datasets    : ADAM.ADXX
*
* Macros used       : %setup, %localsetup, %u_cmp_dset_01, %u_cmp_txt_print, %logcheck_indi
*
* Output files      : @@output
*
* Usage notes       :  
**************************************************************************;
%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/%scan(&_exec_programpath.,8,/)/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

options mprint mlogic symbolgen;
dm "output; clear;";
dm "log; clear;";

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%procprint_indi;

*---------------------------------------------------------------------------------*;
*---------------------------Step 01: Set output name------------------------------*;
*---------------------------------------------------------------------------------*;

%let output = ae200a;


*---------------------------------------------------------------------------------*;
*-------------------------Step 02: Derive dataset for validation------------------*;
*---------------------------------------------------------------------------------*;





data final;
	set 
	label 
;run;

*---------------------------------------------------------------------------------*;
*-------------------------Step 03: Output and Compare-----------------------------*;
*---------------------------------------------------------------------------------*;

data tlf.&output.;
	length COL: $1000.;
		set final(keep=COL:);
		array temp _char_;
		do over temp;
			temp = strip(temp);
		end;
	run;

%u_cmp_dset_01(
base_file_ref=tlf.&output.
,cmpr_file_ref=qctlf.&output.
);

%u_cmp_txt_print;

*---------------------------------------------------------------------------------*;
*-------------------------Step 04: Log Check--------------------------------------*;
*---------------------------------------------------------------------------------*;
%logcheck_indi;









