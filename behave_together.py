#!/usr/bin/env python

import os
import glob
import re
import argparse
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gather BIDS behavioral data across multiple tasks into one wide CSV."
    )

    parser.add_argument(
        "-b", "--bids_dir", required=True,
        help="Path to the top-level BIDS directory."
    )

    # We'll use a mutually exclusive group so the user can EITHER specify tasks OR request all.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-t", "--tasks",
        nargs='+',
        help="Task name(s) to gather (e.g., '-t ADS GNG')."
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Gather data for ALL tasks found via task-*_beh.json in the BIDS root."
    )

    return parser.parse_args()


def main():
    args = parse_args()
    bids_dir = os.path.abspath(args.bids_dir)

    # -------------------------------------------------------------------------
    # Determine which tasks to use, either user-specified (-t) or found in root (--all)
    # -------------------------------------------------------------------------
    if args.all:
        # Look in the BIDS root directory for JSON sidecars of the form task-*_beh.json
        json_pattern = os.path.join(bids_dir, "task-*_beh.json")
        json_files = sorted(glob.glob(json_pattern))
        # Extract the task name from each file. E.g., task-ADS_beh.json -> ADS
        tasks_found = []
        for jf in json_files:
            base = os.path.basename(jf)
            match = re.match(r"task-(.+?)_beh\.json", base)
            if match:
                tasks_found.append(match.group(1))
        if not tasks_found:
            raise ValueError(
                f"No task-*_beh.json files found in {bids_dir} but --all was specified."
            )
        tasks = sorted(set(tasks_found))
        print(f"Detected tasks from BIDS root JSON files: {tasks}")
    else:
        # Use the tasks explicitly provided by the user
        tasks = args.tasks

    # -------------------------------------------------------------------------
    # Read participants.tsv
    # -------------------------------------------------------------------------
    participants_file = os.path.join(bids_dir, "participants.tsv")
    if not os.path.isfile(participants_file):
        raise FileNotFoundError(f"Could not find participants.tsv in {bids_dir}")
    
    participants_df = pd.read_csv(participants_file, sep="\t")

    # If there's a 'participant_id' column, rename to 'subject_id'
    if "participant_id" in participants_df.columns:
        participants_df.rename(columns={"participant_id": "subject_id"}, inplace=True)

    if "subject_id" not in participants_df.columns:
        raise ValueError(
            "participants.tsv must contain a 'subject_id' or 'participant_id' column."
        )

    # Convert participant info to a dict for quick lookups
    # Key = subject_id, Value = dict of all participant data
    participant_info_dict = {}
    for _, row in participants_df.iterrows():
        pid = row["subject_id"]
        participant_info_dict[pid] = row.to_dict()
    
    # -------------------------------------------------------------------------
    # data_dict will hold combined data per (subject_id, session_id)
    # -------------------------------------------------------------------------
    data_dict = {}

    # Find all sub-* directories
    sub_dirs = sorted(glob.glob(os.path.join(bids_dir, "sub-*")))
    
    for sub_dir in sub_dirs:
        subject_id = os.path.basename(sub_dir)  # e.g. sub-001

        # Attempt to find session directories (ses-*)
        ses_dirs = sorted(glob.glob(os.path.join(sub_dir, "ses-*")))
        # If none found, treat the subject folder as a single-session dataset
        if not ses_dirs:
            ses_dirs = [sub_dir]
        
        for ses_dir in ses_dirs:
            # session_id might be 'NA' or "1" if there's no explicit "ses-XX"
            base = os.path.basename(ses_dir)
            if base.startswith("ses-"):
                session_id = base.replace("ses-", "")
            else:
                session_id = "1"  # or "NA"

            # Initialize the (subject, session) entry if not present
            if (subject_id, session_id) not in data_dict:
                data_dict[(subject_id, session_id)] = {}

            # Insert participant-level info
            if subject_id in participant_info_dict:
                for col, val in participant_info_dict[subject_id].items():
                    data_dict[(subject_id, session_id)][col] = val

            # Make sure session_id is stored
            data_dict[(subject_id, session_id)]["session_id"] = session_id

            # -----------------------------------------------------------------
            # For each requested task, try to find *beh.tsv
            # -----------------------------------------------------------------
            for task in tasks:
                beh_pattern = os.path.join(ses_dir, "beh", f"*task-{task}_*beh.tsv")
                matching_files = glob.glob(beh_pattern)
                if not matching_files:
                    continue  # no file for this task

                # If multiple matches, decide how to handle it:
                # We'll just pick the first match for demonstration
                beh_file = matching_files[0]

                # Read the TSV (assuming one row per file)
                beh_df = pd.read_csv(beh_file, sep="\t")
                if len(beh_df) > 1:
                    print(f"Warning: {beh_file} has more than one row. Using row 0 only.")
                row_data = beh_df.iloc[0].to_dict()

                # Optionally prefix columns with the task name to avoid collisions
                # e.g., ADS_ADS-01, ADS_ADS-02, ...
                # Uncomment if needed:
                #
                # prefixed_data = {}
                # for c, v in row_data.items():
                #     # skip participant_id / session_id if present
                #     if c in ["participant_id", "session_id"]:
                #         continue
                #     new_col = f"{task}_{c}"
                #     prefixed_data[new_col] = v
                #
                # row_data = prefixed_data

                # Merge into data_dict
                for c, v in row_data.items():
                    # skip participant_id / session_id if present
                    if c in ["participant_id", "session_id"]:
                        continue
                    data_dict[(subject_id, session_id)][c] = v

    # -------------------------------------------------------------------------
    # Convert dictionary to a DataFrame (one row per subject-session)
    # -------------------------------------------------------------------------
    wide_data = pd.DataFrame.from_dict(list(data_dict.values()))

    # Ensure "session_id" and "subject_id" are present.
    # By design, we put them in data_dict. But let's confirm:
    if "session_id" not in wide_data.columns:
        wide_data["session_id"] = None  # fallback

    if "subject_id" not in wide_data.columns:
        # We'll reconstruct from the keys by matching rows. That means we need 
        # to cross-reference the session_id in each row. Let's do a small approach:
        # The data_dict keys = (subject_id, session_id).
        # The row in wide_data can be matched, for instance, by 'session_id'.
        # But if we have multiple rows with the same session_id for different subjects,
        # that won't work directly. So let's do a direct approach: we'll add a column 
        # in wide_data for subject_id from the dictionary keys.
        # We'll do it by merging back an index:
        # Easiest approach might be to re-create the DataFrame with a row index 
        # from keys, then reset index. Let's do a small step now:

        # First, let's re-build wide_data but keep the index as (subject,session).
        # We'll do that from data_dict directly:
        pairs = []
        for (subj, sess), valdict in data_dict.items():
            # Convert valdict to dict
            row_copy = dict(valdict)
            # Insert subject_id, session_id explicitly
            row_copy["subject_id"] = subj
            row_copy["session_id"] = sess
            pairs.append(row_copy)
        wide_data = pd.DataFrame(pairs)

    # -------------------------------------------------------------------------
    # Reorder columns: subject_id, session_id, plus participant columns, then others
    # -------------------------------------------------------------------------
    front_cols = ["subject_id", "session_id"]
    
    # If participants.tsv had more columns (like age, sex, etc.)
    participant_cols = [c for c in participants_df.columns if c != "subject_id"]
    for c in participant_cols:
        if c not in front_cols and c in wide_data.columns:
            front_cols.append(c)
    
    other_cols = [c for c in wide_data.columns if c not in front_cols]
    final_cols = front_cols + other_cols
    wide_data = wide_data[final_cols]

    # -------------------------------------------------------------------------
    # Build output path: derivatives/phenotype_task-<X>_beh.csv
    # If multiple tasks, join them with '_'.
    # If --all, tasks_str might be "ADS_GNG_XXX..."
    # -------------------------------------------------------------------------
    tasks_str = "_".join(tasks)
    out_dir = os.path.join(bids_dir, "derivatives")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"phenotype_task-{tasks_str}_beh.csv")

    wide_data.to_csv(out_file, index=False)
    print(f"\nSaved combined behavioral data to:\n{out_file}\n")


if __name__ == "__main__":
    main()