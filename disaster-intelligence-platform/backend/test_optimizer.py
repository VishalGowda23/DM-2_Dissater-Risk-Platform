"""Quick test of optimizer pump/cooling allocation and resource gaps"""
import requests

r = requests.post('http://localhost:8000/api/optimize', json={
    'resources': {'pumps': 25, 'buses': 15, 'relief_camps': 12, 'cooling_centers': 20, 'medical_units': 8},
    'scenario': {'use_delta': False}
})
d = r.json()

print('Ward                  flood  heat  pumps cooling buses camps medical')
print('=' * 78)
for w in d['ward_allocations']:
    pumps = w['resources'].get('pumps', {}).get('allocated', 0)
    cool = w['resources'].get('cooling_centers', {}).get('allocated', 0)
    buses = w['resources'].get('buses', {}).get('allocated', 0)
    camps = w['resources'].get('relief_camps', {}).get('allocated', 0)
    med = w['resources'].get('medical_units', {}).get('allocated', 0)
    fl = w['risk']['flood']
    ht = w['risk']['heat']
    print(f'{w["ward_name"]:22s} {fl:5.1f} {ht:5.1f} {pumps:5d} {cool:7d} {buses:5d} {camps:5d} {med:7d}')

total_pumps = sum(w['resources'].get('pumps', {}).get('allocated', 0) for w in d['ward_allocations'])
total_cool = sum(w['resources'].get('cooling_centers', {}).get('allocated', 0) for w in d['ward_allocations'])
print(f'\nTotal pumps: {total_pumps}/25  |  Total cooling: {total_cool}/20')

print('\n=== RESOURCE GAP ===')
for rtype, rdata in d.get('resource_gap', {}).items():
    gap_wards = [w for w in rdata.get('ward_requirements', []) if w['gap'] > 0]
    print(f'{rtype:20s} avail={rdata["total_available"]:3d} req={rdata["total_required"]:3d} gap={rdata["total_gap"]:3d} cov={rdata["coverage_pct"]}%  deficit_wards={len(gap_wards)}')

gs = d.get('resource_gap_summary', {})
print(f'\nOverall: required={gs["total_required"]} available={gs["total_available"]} gap={gs["total_gap"]} coverage={gs["overall_coverage_pct"]}%')
