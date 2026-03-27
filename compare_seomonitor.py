import json
import sys

# Load both files
with open('/Users/user/Downloads/response (4).json', 'r') as f:
    data4 = json.load(f)

with open('/Users/user/Downloads/response (5).json', 'r') as f:
    data5 = json.load(f)

print("=" * 80)
print("SEOMONITOR API RESPONSE COMPARISON: response(4) vs response(5)")
print("=" * 80)

# Basic stats
print(f"\n## BASIC STRUCTURE")
print(f"Response 4: {len(data4)} keywords (type: {type(data4).__name__})")
print(f"Response 5: {len(data5)} keywords (type: {type(data5).__name__})")

if isinstance(data4, list) and isinstance(data5, list):
    kw4 = {item['keyword_id']: item for item in data4}
    kw5 = {item['keyword_id']: item for item in data5}
    
    ids4 = set(kw4.keys())
    ids5 = set(kw5.keys())
    
    common = ids4 & ids5
    only_in_4 = ids4 - ids5
    only_in_5 = ids5 - ids4
    
    print(f"\n## KEYWORD OVERLAP")
    print(f"Common keywords: {len(common)}")
    print(f"Only in response 4: {len(only_in_4)}")
    print(f"Only in response 5: {len(only_in_5)}")
    
    if only_in_4:
        print(f"\n### Keywords ONLY in Response 4 ({len(only_in_4)}):")
        for kid in sorted(only_in_4):
            kw = kw4[kid]
            sv = kw.get('search_data', {}).get('search_volume', 'N/A')
            rank_d = kw.get('ranking_data', {}).get('desktop', {}).get('rank', 'N/A')
            rank_m = kw.get('ranking_data', {}).get('mobile', {}).get('rank', 'N/A')
            print(f"  - [{kid}] \"{kw['keyword']}\" | SV: {sv} | Desktop: {rank_d} | Mobile: {rank_m}")
    
    if only_in_5:
        print(f"\n### Keywords ONLY in Response 5 ({len(only_in_5)}):")
        for kid in sorted(only_in_5):
            kw = kw5[kid]
            sv = kw.get('search_data', {}).get('search_volume', 'N/A')
            rank_d = kw.get('ranking_data', {}).get('desktop', {}).get('rank', 'N/A')
            rank_m = kw.get('ranking_data', {}).get('mobile', {}).get('rank', 'N/A')
            print(f"  - [{kid}] \"{kw['keyword']}\" | SV: {sv} | Desktop: {rank_d} | Mobile: {rank_m}")
    
    print(f"\n## FIELD-BY-FIELD CHANGES IN COMMON KEYWORDS")
    
    rank_changes_desktop = []
    rank_changes_mobile = []
    search_vol_changes = []
    ai_search_changes = []
    intent_changes = []
    label_changes = []
    landing_page_changes = []
    opportunity_changes = []
    serp_changes = []
    traffic_changes = []
    ai_overview_changes = []
    
    for kid in sorted(common):
        k4 = kw4[kid]
        k5 = kw5[kid]
        kw_name = k4['keyword']
        
        r4d = k4.get('ranking_data', {}).get('desktop', {}).get('rank', None)
        r5d = k5.get('ranking_data', {}).get('desktop', {}).get('rank', None)
        r4m = k4.get('ranking_data', {}).get('mobile', {}).get('rank', None)
        r5m = k5.get('ranking_data', {}).get('mobile', {}).get('rank', None)
        
        if r4d != r5d:
            rank_changes_desktop.append((kw_name, r4d, r5d, kid))
        if r4m != r5m:
            rank_changes_mobile.append((kw_name, r4m, r5m, kid))
        
        sv4 = k4.get('search_data', {}).get('search_volume', None)
        sv5 = k5.get('search_data', {}).get('search_volume', None)
        if sv4 != sv5:
            search_vol_changes.append((kw_name, sv4, sv5, kid))
        
        i4 = k4.get('search_intent', None)
        i5 = k5.get('search_intent', None)
        if i4 != i5:
            intent_changes.append((kw_name, i4, i5, kid))
        
        l4 = k4.get('labels', '')
        l5 = k5.get('labels', '')
        if l4 != l5:
            label_changes.append((kw_name, l4, l5, kid))
        
        ai4 = k4.get('ai_search', {})
        ai5 = k5.get('ai_search', {})
        if ai4 != ai5:
            ai_search_changes.append((kw_name, ai4, ai5, kid))
        
        lp4 = k4.get('landing_pages', {})
        lp5 = k5.get('landing_pages', {})
        if lp4 != lp5:
            landing_page_changes.append((kw_name, lp4, lp5, kid))
        
        o4 = k4.get('opportunity', {})
        o5 = k5.get('opportunity', {})
        if o4 != o5:
            opportunity_changes.append((kw_name, o4, o5, kid))

        # SERP data changes
        serp4 = k4.get('serp_data', {})
        serp5 = k5.get('serp_data', {})
        if serp4 != serp5:
            serp_changes.append((kw_name, serp4, serp5, kid))

        # Traffic data changes
        t4 = k4.get('traffic_data', {})
        t5 = k5.get('traffic_data', {})
        if t4 != t5:
            traffic_changes.append((kw_name, t4, t5, kid))

        # AI Overview changes
        aio4 = k4.get('ai_overview', {})
        aio5 = k5.get('ai_overview', {})
        if aio4 != aio5:
            ai_overview_changes.append((kw_name, aio4, aio5, kid))
    
    print(f"\n### Desktop Rank Changes ({len(rank_changes_desktop)}):")
    if rank_changes_desktop:
        rank_changes_desktop.sort(key=lambda x: abs((x[2] or 100) - (x[1] or 100)), reverse=True)
        for kw_name, old, new, kid in rank_changes_desktop[:50]:
            direction = "↑" if (new or 100) < (old or 100) else "↓"
            diff = (old or 100) - (new or 100)
            print(f"  {direction} \"{kw_name}\" [{kid}]: {old} -> {new} ({'+' if diff > 0 else ''}{diff})")
    else:
        print("  No desktop ranking changes found.")
    
    print(f"\n### Mobile Rank Changes ({len(rank_changes_mobile)}):")
    if rank_changes_mobile:
        rank_changes_mobile.sort(key=lambda x: abs((x[2] or 100) - (x[1] or 100)), reverse=True)
        for kw_name, old, new, kid in rank_changes_mobile[:50]:
            direction = "↑" if (new or 100) < (old or 100) else "↓"
            diff = (old or 100) - (new or 100)
            print(f"  {direction} \"{kw_name}\" [{kid}]: {old} -> {new} ({'+' if diff > 0 else ''}{diff})")
    else:
        print("  No mobile ranking changes found.")
    
    print(f"\n### Search Volume Changes ({len(search_vol_changes)}):")
    if search_vol_changes:
        search_vol_changes.sort(key=lambda x: abs((x[2] or 0) - (x[1] or 0)), reverse=True)
        for kw_name, old, new, kid in search_vol_changes[:30]:
            print(f"  \"{kw_name}\" [{kid}]: {old} -> {new}")
    else:
        print("  No search volume changes found.")
    
    print(f"\n### Search Intent Changes ({len(intent_changes)}):")
    if intent_changes:
        for kw_name, old, new, kid in intent_changes:
            print(f"  \"{kw_name}\" [{kid}]: {old} -> {new}")
    else:
        print("  No intent changes found.")
    
    print(f"\n### Label Changes ({len(label_changes)}):")
    if label_changes:
        for kw_name, old, new, kid in label_changes:
            print(f"  \"{kw_name}\" [{kid}]: \"{old}\" -> \"{new}\"")
    else:
        print("  No label changes found.")
    
    print(f"\n### AI Search Changes ({len(ai_search_changes)}):")
    if ai_search_changes:
        for kw_name, old, new, kid in ai_search_changes[:30]:
            diffs = []
            for key in set(list(old.keys()) + list(new.keys())):
                if old.get(key) != new.get(key):
                    diffs.append(f"{key}: {old.get(key)} -> {new.get(key)}")
            print(f"  \"{kw_name}\" [{kid}]: {', '.join(diffs)}")
    else:
        print("  No AI search changes found.")
    
    print(f"\n### AI Overview Changes ({len(ai_overview_changes)}):")
    if ai_overview_changes:
        for kw_name, old, new, kid in ai_overview_changes[:30]:
            diffs = []
            for device in ['desktop', 'mobile']:
                od = old.get(device, {})
                nd = new.get(device, {})
                for key in set(list(od.keys()) + list(nd.keys())):
                    if od.get(key) != nd.get(key):
                        diffs.append(f"{device}.{key}: {od.get(key)} -> {nd.get(key)}")
            print(f"  \"{kw_name}\" [{kid}]: {', '.join(diffs)}")
    else:
        print("  No AI overview changes found.")

    print(f"\n### Landing Page Changes ({len(landing_page_changes)}):")
    if landing_page_changes:
        for kw_name, old, new, kid in landing_page_changes[:20]:
            diffs = []
            for device in ['desktop', 'mobile']:
                for page_type in ['current', 'desired']:
                    o = old.get(device, {}).get(page_type, '')
                    n = new.get(device, {}).get(page_type, '')
                    if o != n:
                        diffs.append(f"{device} {page_type}: {o} -> {n}")
            print(f"  \"{kw_name}\" [{kid}]: {'; '.join(diffs)}")
    else:
        print("  No landing page changes found.")
    
    print(f"\n### Opportunity Score Changes ({len(opportunity_changes)}):")
    if opportunity_changes:
        for kw_name, old, new, kid in opportunity_changes[:20]:
            diffs = []
            for key in set(list(old.keys()) + list(new.keys())):
                if old.get(key) != new.get(key):
                    diffs.append(f"{key}: {old.get(key)} -> {new.get(key)}")
            print(f"  \"{kw_name}\" [{kid}]: {', '.join(diffs)}")
    else:
        print("  No opportunity changes found.")

    print(f"\n### SERP Feature Changes ({len(serp_changes)}):")
    if serp_changes:
        print(f"  {len(serp_changes)} keywords have SERP feature differences (too detailed to list all)")
        # Show a few examples
        for kw_name, old, new, kid in serp_changes[:5]:
            print(f"  Example: \"{kw_name}\" [{kid}]")
            pct4 = old.get('percentage_clicks', 'N/A')
            pct5 = new.get('percentage_clicks', 'N/A')
            if pct4 != pct5:
                print(f"    percentage_clicks: {pct4} -> {pct5}")
    else:
        print("  No SERP feature changes found.")

    print(f"\n### Traffic Data Changes ({len(traffic_changes)}):")
    if traffic_changes:
        for kw_name, old, new, kid in traffic_changes[:20]:
            diffs = []
            for key in set(list(old.keys()) + list(new.keys())):
                if old.get(key) != new.get(key):
                    diffs.append(f"{key}: {old.get(key)} -> {new.get(key)}")
            print(f"  \"{kw_name}\" [{kid}]: {', '.join(diffs)}")
    else:
        print("  No traffic data changes found.")
    
    # Overall summary
    changed_kw_ids = set(
        [x[3] for x in rank_changes_desktop] + [x[3] for x in rank_changes_mobile] +
        [x[3] for x in search_vol_changes] + [x[3] for x in intent_changes] +
        [x[3] for x in label_changes] + [x[3] for x in ai_search_changes] +
        [x[3] for x in landing_page_changes] + [x[3] for x in opportunity_changes] +
        [x[3] for x in serp_changes] + [x[3] for x in traffic_changes] +
        [x[3] for x in ai_overview_changes]
    )
    no_changes = len(common) - len(changed_kw_ids)
    
    print(f"\n## SUMMARY")
    print(f"  Total keywords in response 4: {len(data4)}")
    print(f"  Total keywords in response 5: {len(data5)}")
    print(f"  Common keywords: {len(common)}")
    print(f"  Only in response 4: {len(only_in_4)}")
    print(f"  Only in response 5: {len(only_in_5)}")
    print(f"  ---")
    print(f"  Keywords with ANY difference: {len(changed_kw_ids)}")
    print(f"  Keywords identical: {no_changes}")
    print(f"  ---")
    print(f"  Desktop rank changes: {len(rank_changes_desktop)}")
    print(f"  Mobile rank changes: {len(rank_changes_mobile)}")
    print(f"  Search volume changes: {len(search_vol_changes)}")
    print(f"  Intent changes: {len(intent_changes)}")
    print(f"  Label changes: {len(label_changes)}")
    print(f"  AI search changes: {len(ai_search_changes)}")
    print(f"  AI overview changes: {len(ai_overview_changes)}")
    print(f"  Landing page changes: {len(landing_page_changes)}")
    print(f"  Opportunity changes: {len(opportunity_changes)}")
    print(f"  SERP feature changes: {len(serp_changes)}")
    print(f"  Traffic data changes: {len(traffic_changes)}")

    # Structural comparison
    print(f"\n## STRUCTURAL COMPARISON")
    if common:
        sample_id = list(common)[0]
        keys4 = set(kw4[sample_id].keys())
        keys5 = set(kw5[sample_id].keys())
        if keys4 == keys5:
            print(f"  Both responses have identical top-level fields: {sorted(keys4)}")
        else:
            print(f"  Fields only in response 4: {keys4 - keys5}")
            print(f"  Fields only in response 5: {keys5 - keys4}")
            print(f"  Common fields: {keys4 & keys5}")

print("\n" + "=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80)
