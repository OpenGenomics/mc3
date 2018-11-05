#!/bin/bash
#$ -cwd
#$ -j y
#$ -S /bin/bash
#$ -V

function usage()
{
        echo "makeJSON.sh"
        echo "Kami E. Chiotti 10.15.18"
        echo
        echo "Takes user-edited template for CWL Workflow Tool input options and converts to JSON file"
        echo
        echo "Usage: $0 [-i INPUT_TEMPLATE] [-p SAMPLE_LIST] [-o OUTPUT_PREFIX] "
        echo
        echo "Required:"
        echo "  [-i INPUT_TEMPLATE]  - Full path to CWL Workflow Tool file."
        echo
        echo "Optional:"
        echo "  [-o OUTPUT_PREFIX]   - Prefix for output JSON filename [defaults to 'input' when $SAMPLE_LIST is NOT provided,"
        echo "                         ignored when $SAMPLE_LIST is provided]"
        echo "  [-p SAMPLE_LIST]     - Required if using SAMPLE_LIST; full path to a tab-delimited file"
        exit
}

INPUT_TEMPLATE=""
OUTPUT_PREFIX=""
SAMPLE_LIST=""

while getopts ":i:o:p:h" Option
        do
        case $Option in
                i ) INPUT_TEMPLATE="$OPTARG" ;;
                o ) OUTPUT_PREFIX="$OPTARG" ;;
                p ) SAMPLE_LIST="$OPTARG" ;;
                h ) usage ;;
                * ) echo "unrecognized argument. use '-h' for usage information."; exit -1 ;;
        esac
done
shift $(($OPTIND - 1))

if [ "$INPUT_TEMPLATE" == "" ]
then
        usage
fi
if [ ! -f "$INPUT_TEMPLATE" ]
then
  echo "ERROR: Input template file does not exist."
  exit 1
fi
if [[ "$SAMPLE_LIST" != "" && ! -f "$SAMPLE_LIST" ]]
then
  echo "ERROR: Sample file does not exist."
  exit 1
fi
  if [[ -z "$OUTPUT_PREFIX" && "$SAMPLE_LIST" == "" ]]
  then
    OUTPUT_PREFIX=input
  else
    OUTPUT_PREFIX=tmp
  fi

ABS_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ignore=("class" "path")
num=`wc -l $INPUT_TEMPLATE | cut -d' ' -f1`
snum=`wc -l $SAMPLE_LIST | cut -d' ' -f1`

##########################################################################
###### FUNCTIONS #########################################################
##########################################################################

function chky()
{
  eval "declare -A cklist="${2#*=}	# work around for bash version 4.2.46
#  local -n cklist=$2			# for bash version 4.3 or higher
  mtch=0
  for ele in "${cklist[@]}"
  do
    ((mtch++))
    if [[ $1 == "$ele" ]]
    then
      echo $mtch
    fi
  done
}

function keyval()
{
  if [[ $2 =~ ^[0-9]+([.][0-9]+)?$ || $2 == [\[{] ]]
  then
    echo "\"$1\" : $2"
  elif [[ $2 == "true" || $2 == "false" || $2 == "null" || ${2:0:1} == "\$" ]]
  then
    if [[ $3 == $num ]]
    then
      echo "\"$1\" : $2"
    else
      echo "\"$1\" : $2,"
    fi
  else
    if [[ $3 == $num ]]
    then
      echo "\"$1\" : \"$2\""
    else
      echo "\"$1\" : \"$2\","
    fi
  fi
}

function loop_ary()
{
  cls=$1
  IFS=' ' read -a eles <<< `(echo $2 | sed 's/,/ /g')`
  idx=`expr ${#eles[@]} - 1`
  i=0
  echo "        {"
  for ele in ${eles[@]}
  do
    echo "            \"class\" : \"$cls\","
    echo "            \"path\" : $ele"
    if [[ $i == $idx ]]
    then
      echo "        }"
    else
      echo "        },"
    fi
    ((i++))
  done
  IFS=$'\n'  
}

function single_json()     # args: template file, output filename
{
  tmplt=$1; outjsn=$2; lnum=0; varnum=1; ary_type=''; all_keys=()
  
  echo "{" > $outjsn
  IFS=$'\n'
  for LINE in $(cat $tmplt)    # LINE=`sed "${lnum}q;d" $tmplt`
  do
    ((lnum++))
    line=`echo $LINE | sed 's/ //g' | cut -d# -f1`
    ky=`echo $line | cut -d: -f1`
    vl=`echo $line | cut -d: -f2`
    if [[ $vl == "<>" ]]
    then
      vl=\$$varnum
      ((varnum++))
    fi
    if [[ ${LINE:0:1} == "#" ]]    # don't write these lines
    then
      continue
    elif [[ (-z $vl && ${LINE:0:1} != "#") || (-z $ky && ${LINE:0:1} != "#") ]]    # error if $ky or $vl is empty
    then
      echo "Template format error on line $lnum of template"
      exit 1
    elif [[ $ky == "-class" ]]
    then
      ary_type=$vl               # set $ary_type for expected next input key="-path"
    elif [[ $ky == "-path" ]]
    then
      if [[ ! -z $ary_type ]]    # $ary_type = Directory/File
      then
        loop_ary $ary_type $vl  # write array of File or Directory
        ary_type=''
        if [[ $lnum == $num ]]
        then
          echo "    ]"
        else
          echo "    ],"
        fi
      else
        echo "Template format error on line $lnum; '- class' must be provided before '- path'"   # "-path" found but $ary_type not set
        exit 1
      fi
    elif [[ ${ky:0:2} == "-\"" ]]
    then
      echo "        {"
      echo "            ${ky:1:${#ky}}"
      echo "        }"
      if [[ $lnum == $num ]]
      then
        echo "    ]"
      else
        echo "    ],"
      fi
    elif [[ -z `chky $ky "$(declare -p ignore)"` ]]	 # work around for bash version 4.2.46
#    elif [[ -z `chky $ky ignore` ]]     		 # for bash version 4.3 or higher
    then
        echo "    `keyval $ky $vl $lnum`"
        all_keys+=($ky)
    elif [[ `chky $ky "$(declare -p ignore)"` > 0 ]]     # work around for bash version 4.2.46
#    elif [[ `chky $ky ignore` > 0 ]]			 # for bash version 4.3 or higher
    then
      if [[ ($ky == "path") ]]
      then
        echo "        `keyval $ky $vl $num`"
        if [[ $lnum == $num ]]
        then
          echo "    }"
        else
          echo "    },"
        fi
      else
        echo "        `keyval $ky $vl $lnum`"
      fi
    else
      echo "what am I missing at line $lnum or variable $varnum?"
    fi
  done
  echo "}"  
  unset IFS
}

function write_script()
{
  eval "declare -A args="${2#*=}		      # work around for bash version 4.2.46
#  local -n args=$2				      # for bash version 4.3 or higher
  basejsn=$1
  arglen=`echo ${#args[@]}`
  echo '#!/bin/bash'
  echo
  echo "cat <<EOF"
  cat $basejsn
  echo "EOF"
}

function multi_json()
{
  mkdir -p json_queue
  cd json_queue
  tmplt=../$1; slist=../$2; outjsn=$3  

  single_json $tmplt $outjsn >> $outjsn 	# write tmp.json with variables to fill from sample list
  IFS=' ' read -a hdr <<< `(head -n 1 $slist | sed 's/://g')`
  
  IFS=$'\n'
  idxs=()
  for key in "${all_keys[@]}"           # get order in which keys were read from template
  do
    idx=`chky $key "$(declare -p hdr)"`		   # work around for bash version 4.2.46
#    idx=`chky $key hdr`			   # for bash version 4.3 or higher
    if [[ ! -z $idx ]]
    then
      idxs+=(\$$idx)                    # place arguments in order for running popJSON.sh
    fi
  done

   write_script $outjsn "$(declare -p idxs)" > popJSON.sh       # work around for bash version 4.2.46
#  write_script $outjsn idxs > popJSON.sh 	 		# write script to fill from sample list; for bash version 4.3 or higher
 
  slnum=0
  for LINE in $(cat $slist)
  do
    ((slnum++))
    if [[ $slnum == 1 ]]
    then
      continue
    else
      arg_list=()
      rid=`awk 'FNR=='$slnum' {print $1}' < $slist`
      for i in ${idxs[@]}
      do
        fld=`echo $i`
        arg_list+=(`awk 'FNR=='$slnum' {print '$fld'}' < $slist`)
      done
           
      sh popJSON.sh ${arg_list[@]} > $rid.json   # run script for each input sample in list
    fi
  done
  rm -f popJSON.sh tmp.json
  cd ..
  unset IFS
}

##########################################################################
###### MAIN ##############################################################
##########################################################################

uid=`date +%Y%m%d-%R%S | sed 's/://g'`
logfile="$uid.log.txt"
{

  if [[ "$SAMPLE_LIST" != "" ]]
  then
    multi_json $INPUT_TEMPLATE $SAMPLE_LIST $OUTPUT_PREFIX.json
  else
    single_json $INPUT_TEMPLATE $OUTPUT_PREFIX.json > $OUTPUT_PREFIX.json
  fi

} > $logfile 2>&1

