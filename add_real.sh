#!/bin/bash 

CASE_SCRIPT=$(realpath ${1:-case_config.ini})
SITE_SCRIPT=$(realpath ${2:-site_config.ini})

# get case-specifig config paths (overriding defaults)
if [ -f "${CASE_SCRIPT}" ]; then
  sed -e "s@\[CASE\]@#!/bin/bash@" "${CASE_SCRIPT}" > case_config
  . case_config
fi

# get site-specifig config paths (overriding defaults)
if [ -f "${SITE_SCRIPT}" ]; then
  sed -e "s@\[SITE\]@#!/bin/bash@" "${SITE_SCRIPT}" > site_config
  . site_config
fi

function min {
   ( [ $1 -le $2 ] && echo $1 ) || ( [ $2 -lt $1 ] && echo $2 ) 
}

function value {
    string=$1;
    file=$2;
    line=$(grep "^$string" $file); 
    echo "${line##* }"
}

list_brains=$( ls $DATA_PATH/t1-1mm-1 )
echo ${list_brains[*]}
for brainid in ${list_brains[*]}; do
    #echo $brainid
    dir_session=$DATA_PATH/t1-1mm-1/$brainid/t1mri/default_acquisition/default_analysis/folds/3.3/session1_manual
    Lbrain=$dir_session/L${brainid}_session1_manual.arg
    Rbrain=$dir_session/R${brainid}_session1_manual.arg
    #ls $Lbrain $Rbrain
    bhal=$( value "brain_hull_area" $Lbrain )
    bhar=$( value "brain_hull_area" $Rbrain )
    bhvl=$( value "brain_hull_volume" $Lbrain )
    bhvr=$( value "brain_hull_volume" $Rbrain  )
    #echo $bhal,$bhar, $bhvl,$bhvr
    
    sed '0,/"Todo",/s//"{01_bhal, 38000,'$bhal',  55000}","{02_bhar, 38000,'$bhar',  55000}","{03_bhvl,500000,'$bhvl',830000}","{04_bhvr,500000,'$bhvr',830000}",/' -i $CASE_DATA_CONFIG
done
