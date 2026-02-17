"""Initial schema - wards, risk scores, users, audit logs"""

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


def upgrade() -> None:
    # Create PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Wards table
    op.create_table(
        'wards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ward_id', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('zone', sa.String(100)),
        sa.Column('centroid_lat', sa.Float()),
        sa.Column('centroid_lon', sa.Float()),
        sa.Column('area_sq_km', sa.Float()),
        sa.Column('geometry', Geometry('MULTIPOLYGON', srid=4326)),
        sa.Column('population', sa.Integer()),
        sa.Column('population_density', sa.Float()),
        sa.Column('elderly_ratio', sa.Float()),
        sa.Column('settlement_pct', sa.Float()),
        sa.Column('elevation_m', sa.Float()),
        sa.Column('mean_slope', sa.Float()),
        sa.Column('min_elevation_m', sa.Float()),
        sa.Column('max_elevation_m', sa.Float()),
        sa.Column('low_lying_index', sa.Float()),
        sa.Column('drainage_index', sa.Float()),
        sa.Column('impervious_surface_pct', sa.Float()),
        sa.Column('hospital_count', sa.Integer()),
        sa.Column('fire_station_count', sa.Integer()),
        sa.Column('shelter_count', sa.Integer()),
        sa.Column('school_count', sa.Integer()),
        sa.Column('road_density_km', sa.Float()),
        sa.Column('infrastructure_density', sa.Float()),
        sa.Column('historical_flood_events', sa.Integer()),
        sa.Column('historical_flood_frequency', sa.Float()),
        sa.Column('avg_annual_rainfall_mm', sa.Float()),
        sa.Column('historical_heatwave_days', sa.Integer()),
        sa.Column('baseline_avg_rainfall_mm', sa.Float()),
        sa.Column('baseline_avg_temp_c', sa.Float()),
        sa.Column('data_completeness', sa.Float()),
        sa.Column('last_weather_update', sa.DateTime()),
        sa.Column('last_osm_update', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Ward Risk Scores table
    op.create_table(
        'ward_risk_scores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ward_id', sa.String(20), sa.ForeignKey('wards.ward_id'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('flood_baseline_risk', sa.Float()),
        sa.Column('heat_baseline_risk', sa.Float()),
        sa.Column('flood_event_risk', sa.Float()),
        sa.Column('heat_event_risk', sa.Float()),
        sa.Column('flood_risk_delta', sa.Float()),
        sa.Column('flood_risk_delta_pct', sa.Float()),
        sa.Column('heat_risk_delta', sa.Float()),
        sa.Column('heat_risk_delta_pct', sa.Float()),
        sa.Column('ml_flood_probability', sa.Float()),
        sa.Column('ml_heat_probability', sa.Float()),
        sa.Column('ml_confidence', sa.Float()),
        sa.Column('final_flood_risk', sa.Float()),
        sa.Column('final_heat_risk', sa.Float()),
        sa.Column('final_combined_risk', sa.Float()),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('uncertainty_score', sa.Float()),
        sa.Column('neighbor_spillover_applied', sa.Boolean(), default=False),
        sa.Column('spillover_source_wards', sa.JSON()),
        sa.Column('current_rainfall_mm', sa.Float()),
        sa.Column('rainfall_forecast_48h_mm', sa.Float()),
        sa.Column('current_temp_c', sa.Float()),
        sa.Column('temp_anomaly_c', sa.Float()),
        sa.Column('weather_condition', sa.String(50)),
        sa.Column('wind_speed_kmh', sa.Float()),
        sa.Column('humidity_pct', sa.Float()),
        sa.Column('rainfall_forecast_7d_mm', sa.Float()),
        sa.Column('top_hazard', sa.String(20)),
        sa.Column('top_risk_score', sa.Float()),
        sa.Column('risk_category', sa.String(20), index=True),
        sa.Column('surge_alert', sa.Boolean(), default=False),
        sa.Column('critical_alert', sa.Boolean(), default=False),
        sa.Column('alert_message', sa.Text()),
        sa.Column('risk_factors', sa.JSON()),
        sa.Column('top_drivers', sa.JSON()),
        sa.Column('shap_values', sa.JSON()),
        sa.Column('recommendations', sa.JSON()),
    )

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(100), unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), default='viewer'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime()),
    )

    # Audit Log table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('username', sa.String(50)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource', sa.String(100)),
        sa.Column('details', sa.JSON()),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create spatial index
    op.create_index('idx_wards_geometry', 'wards', ['geometry'], postgresql_using='gist')


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('ward_risk_scores')
    op.drop_index('idx_wards_geometry', table_name='wards')
    op.drop_table('wards')
