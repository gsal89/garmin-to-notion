- name: Sync activities to Notion
  env:
    GARTH_HOME: ${{ runner.temp }}/.garth
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    NOTION_DB_ID: ${{ secrets.NOTION_DB_ID }}
    NOTION_PR_DB_ID: ${{ secrets.NOTION_PR_DB_ID }}
    NOTION_STEPS_DB_ID: ${{ secrets.NOTION_STEPS_DB_ID }}
    NOTION_SLEEP_DB_ID: ${{ secrets.NOTION_SLEEP_DB_ID }}
    GARMIN_ACTIVITIES_FETCH_LIMIT: ${{ vars.GARMIN_ACTIVITIES_FETCH_LIMIT }}
    TZ: 'Australia/Perth'
  run: |
    python sync_with_garth.py
