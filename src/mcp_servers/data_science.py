#!/usr/bin/env python3
"""
Data Science MCP Server for ZEJZL.NET
Provides data analysis tools for AI applications including:
- Data profiling and statistics
- Data visualization generation
- Correlation analysis
- Outlier detection
- Data quality assessment
"""

import asyncio
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import tempfile
import base64
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_servers.base_server import BaseMCPServer


class DataScienceMCPServer(BaseMCPServer):
    """
    MCP Server for data science operations
    Provides tools for analyzing datasets, generating visualizations, and statistical analysis
    """

    def __init__(self):
        super().__init__("data_science", "1.0.0")
        self.supported_formats = ['.csv', '.json', '.xlsx', '.xls', '.parquet', '.feather']

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return available tools for data science"""
        return [
            {
                "name": "analyze_dataset",
                "description": "Analyze dataset structure and basic statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        },
                        "sample_size": {
                            "type": "integer",
                            "description": "Number of rows to sample for analysis",
                            "default": 1000
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "calculate_statistics",
                "description": "Calculate comprehensive statistics for numerical columns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific columns to analyze (optional)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "find_correlations",
                "description": "Find correlations between numerical variables",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        },
                        "method": {
                            "type": "string",
                            "description": "Correlation method",
                            "enum": ["pearson", "spearman", "kendall"],
                            "default": "pearson"
                        },
                        "min_correlation": {
                            "type": "number",
                            "description": "Minimum absolute correlation to report",
                            "default": 0.3
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "detect_outliers",
                "description": "Detect outliers using statistical methods",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        },
                        "column": {
                            "type": "string",
                            "description": "Column to analyze for outliers"
                        },
                        "method": {
                            "type": "string",
                            "description": "Outlier detection method",
                            "enum": ["iqr", "zscore", "isolation_forest"],
                            "default": "iqr"
                        }
                    },
                    "required": ["path", "column"]
                }
            },
            {
                "name": "generate_visualization",
                "description": "Generate data visualization as base64 image",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        },
                        "plot_type": {
                            "type": "string",
                            "description": "Type of visualization",
                            "enum": ["histogram", "scatter", "boxplot", "correlation_heatmap"],
                            "default": "histogram"
                        },
                        "x_column": {
                            "type": "string",
                            "description": "X-axis column"
                        },
                        "y_column": {
                            "type": "string",
                            "description": "Y-axis column (for scatter/boxplot)"
                        }
                    },
                    "required": ["path", "x_column"]
                }
            },
            {
                "name": "assess_data_quality",
                "description": "Assess data quality and identify issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to dataset file"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

    def _load_dataset(self, path: str, sample_size: int = None) -> pd.DataFrame:
        """Load dataset from file with automatic format detection"""
        if not os.path.exists(path):
            raise ValueError(f"File does not exist: {path}")

        file_ext = Path(path).suffix.lower()

        try:
            if file_ext == '.csv':
                df = pd.read_csv(path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(path)
            elif file_ext == '.json':
                df = pd.read_json(path)
            elif file_ext == '.parquet':
                df = pd.read_parquet(path)
            elif file_ext == '.feather':
                df = pd.read_feather(path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Sample if requested
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=42)

            return df

        except Exception as e:
            raise ValueError(f"Failed to load dataset: {e}")

    async def _analyze_dataset(self, path: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Analyze dataset structure and basic statistics"""
        df = self._load_dataset(path, sample_size)

        # Basic info
        info = {
            'shape': df.shape,
            'columns': len(df.columns),
            'rows': len(df),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }

        # Column analysis
        columns_info = {}
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'non_null_count': df[col].notna().sum(),
                'null_count': df[col].isna().sum(),
                'null_percentage': (df[col].isna().sum() / len(df)) * 100
            }

            # Type-specific analysis
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    'min': float(df[col].min()) if not df[col].empty else None,
                    'max': float(df[col].max()) if not df[col].empty else None,
                    'mean': float(df[col].mean()) if not df[col].empty else None,
                    'std': float(df[col].std()) if not df[col].empty else None,
                    'unique_values': df[col].nunique()
                })
            elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                col_info.update({
                    'unique_values': df[col].nunique(),
                    'most_common': df[col].value_counts().head(5).to_dict() if not df[col].empty else {}
                })

            columns_info[col] = col_info

        return {
            'dataset_info': info,
            'columns': columns_info,
            'sample_data': df.head(5).to_dict('records')
        }

    async def _calculate_statistics(self, path: str, columns: List[str] = None) -> Dict[str, Any]:
        """Calculate comprehensive statistics for numerical columns"""
        df = self._load_dataset(path)

        # Filter to numerical columns or specified columns
        if columns:
            available_cols = [col for col in columns if col in df.columns]
            if not available_cols:
                raise ValueError("None of the specified columns exist in the dataset")
            num_cols = [col for col in available_cols if pd.api.types.is_numeric_dtype(df[col])]
        else:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not num_cols:
            return {'error': 'No numerical columns found in dataset'}

        # Calculate statistics
        stats = {}
        for col in num_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            # Basic stats
            basic_stats = series.describe().to_dict()

            # Additional stats
            additional_stats = {
                'skewness': float(series.skew()),
                'kurtosis': float(series.kurtosis()),
                'variance': float(series.var()),
                'range': float(series.max() - series.min()),
                'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
                'cv': float(series.std() / series.mean()) if series.mean() != 0 else float('inf')
            }

            # Quartiles
            quartiles = {
                'q1': float(series.quantile(0.25)),
                'q2_median': float(series.quantile(0.5)),
                'q3': float(series.quantile(0.75))
            }

            stats[col] = {
                'basic': basic_stats,
                'additional': additional_stats,
                'quartiles': quartiles
            }

        return {
            'numerical_columns': num_cols,
            'statistics': stats
        }

    async def _find_correlations(self, path: str, method: str = "pearson",
                                min_correlation: float = 0.3) -> Dict[str, Any]:
        """Find correlations between numerical variables"""
        df = self._load_dataset(path)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(num_cols) < 2:
            return {'error': 'Need at least 2 numerical columns for correlation analysis'}

        # Calculate correlation matrix
        corr_matrix = df[num_cols].corr(method=method)

        # Find significant correlations
        correlations = []
        for i, col1 in enumerate(num_cols):
            for j, col2 in enumerate(num_cols):
                if i < j:  # Only upper triangle
                    corr_value = corr_matrix.loc[col1, col2]
                    if abs(corr_value) >= min_correlation:
                        correlations.append({
                            'variable1': col1,
                            'variable2': col2,
                            'correlation': float(corr_value),
                            'strength': self._get_correlation_strength(abs(corr_value))
                        })

        # Sort by absolute correlation strength
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

        return {
            'method': method,
            'numerical_columns': num_cols,
            'correlation_matrix': corr_matrix.to_dict(),
            'significant_correlations': correlations,
            'total_significant': len(correlations)
        }

    def _get_correlation_strength(self, corr: float) -> str:
        """Get correlation strength description"""
        if corr >= 0.8:
            return 'very_strong'
        elif corr >= 0.6:
            return 'strong'
        elif corr >= 0.4:
            return 'moderate'
        elif corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'

    async def _detect_outliers(self, path: str, column: str, method: str = "iqr") -> Dict[str, Any]:
        """Detect outliers using statistical methods"""
        df = self._load_dataset(path)

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataset")

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"Column '{column}' is not numerical")

        series = df[column].dropna()
        if len(series) == 0:
            return {'error': 'No valid data in column'}

        outliers = []
        outlier_indices = []

        if method == "iqr":
            # IQR method
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outlier_mask = (series < lower_bound) | (series > upper_bound)
            outliers = series[outlier_mask].tolist()
            outlier_indices = series[outlier_mask].index.tolist()

        elif method == "zscore":
            # Z-score method
            z_scores = np.abs((series - series.mean()) / series.std())
            outlier_mask = z_scores > 3
            outliers = series[outlier_mask].tolist()
            outlier_indices = series[outlier_mask].index.tolist()

        elif method == "isolation_forest":
            # Isolation Forest (requires scikit-learn)
            try:
                from sklearn.ensemble import IsolationForest
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                outlier_predictions = iso_forest.fit_predict(series.values.reshape(-1, 1))

                outlier_mask = outlier_predictions == -1
                outliers = series[outlier_mask].tolist()
                outlier_indices = series[outlier_mask].index.tolist()
            except ImportError:
                return {'error': 'scikit-learn required for isolation forest method'}

        return {
            'column': column,
            'method': method,
            'total_values': len(series),
            'outlier_count': len(outliers),
            'outlier_percentage': (len(outliers) / len(series)) * 100,
            'outliers': outliers[:100],  # Limit for response size
            'outlier_indices': outlier_indices[:100]
        }

    async def _generate_visualization(self, path: str, plot_type: str = "histogram",
                                     x_column: str = None, y_column: str = None) -> Dict[str, Any]:
        """Generate data visualization as base64 image"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            return {'error': 'matplotlib and seaborn required for visualization'}

        df = self._load_dataset(path)

        if x_column and x_column not in df.columns:
            raise ValueError(f"Column '{x_column}' not found in dataset")

        if y_column and y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' not found in dataset")

        # Create plot
        plt.figure(figsize=(10, 6))
        plt.style.use('default')

        try:
            if plot_type == "histogram":
                if not x_column:
                    return {'error': 'x_column required for histogram'}
                if not pd.api.types.is_numeric_dtype(df[x_column]):
                    return {'error': 'Histogram requires numerical column'}

                sns.histplot(data=df, x=x_column, kde=True)
                plt.title(f"Distribution of {x_column}")

            elif plot_type == "scatter":
                if not x_column or not y_column:
                    return {'error': 'Both x_column and y_column required for scatter plot'}
                if not pd.api.types.is_numeric_dtype(df[x_column]) or not pd.api.types.is_numeric_dtype(df[y_column]):
                    return {'error': 'Scatter plot requires numerical columns'}

                sns.scatterplot(data=df, x=x_column, y=y_column)
                plt.title(f"{y_column} vs {x_column}")

            elif plot_type == "boxplot":
                if not x_column:
                    return {'error': 'x_column required for boxplot'}
                if not pd.api.types.is_numeric_dtype(df[x_column]):
                    return {'error': 'Boxplot requires numerical column'}

                sns.boxplot(data=df, y=x_column)
                plt.title(f"Boxplot of {x_column}")

            elif plot_type == "correlation_heatmap":
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(num_cols) < 2:
                    return {'error': 'Need at least 2 numerical columns for correlation heatmap'}

                corr_matrix = df[num_cols].corr()
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
                plt.title("Correlation Heatmap")

            else:
                return {'error': f'Unsupported plot type: {plot_type}'}

            # Convert plot to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            plt.close()

            return {
                'plot_type': plot_type,
                'image_base64': image_base64,
                'image_format': 'png',
                'columns_used': [col for col in [x_column, y_column] if col]
            }

        except Exception as e:
            plt.close()
            return {'error': f'Failed to generate visualization: {e}'}

    async def _assess_data_quality(self, path: str) -> Dict[str, Any]:
        """Assess data quality and identify issues"""
        df = self._load_dataset(path)

        quality_issues = []
        quality_score = 100

        # Check for missing values
        missing_data = df.isnull().sum()
        total_missing = missing_data.sum()

        if total_missing > 0:
            missing_percentage = (total_missing / (len(df) * len(df.columns))) * 100
            quality_score -= min(missing_percentage * 2, 30)  # Max 30 point deduction

            # Find columns with high missing rates
            high_missing_cols = missing_data[missing_data > len(df) * 0.1]
            if len(high_missing_cols) > 0:
                quality_issues.append({
                    'type': 'high_missing_values',
                    'severity': 'high',
                    'description': f"Columns with >10% missing values: {high_missing_cols.index.tolist()}",
                    'affected_columns': high_missing_cols.index.tolist()
                })

        # Check for duplicate rows
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            duplicate_percentage = (duplicate_rows / len(df)) * 100
            quality_score -= min(duplicate_percentage, 20)  # Max 20 point deduction

            quality_issues.append({
                'type': 'duplicate_rows',
                'severity': 'medium',
                'description': f"Found {duplicate_rows} duplicate rows ({duplicate_percentage:.1f}%)",
                'count': int(duplicate_rows)
            })

        # Check for inconsistent data types
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                # Try to infer if it should be numeric
                try:
                    pd.to_numeric(df[col].dropna())
                    quality_issues.append({
                        'type': 'potential_numeric_column',
                        'severity': 'low',
                        'description': f"Column '{col}' contains strings that could be numeric",
                        'column': col
                    })
                except:
                    pass

        # Check for outliers in numerical columns
        num_cols = df.select_dtypes(include=[np.number]).columns
        outlier_cols = []

        for col in num_cols:
            series = df[col].dropna()
            if len(series) > 10:  # Only check if enough data
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((series < (Q1 - 1.5 * IQR)) | (series > (Q3 + 1.5 * IQR))).sum()

                if outliers > len(series) * 0.05:  # More than 5% outliers
                    outlier_cols.append(col)

        if outlier_cols:
            quality_issues.append({
                'type': 'potential_outliers',
                'severity': 'medium',
                'description': f"Columns with potential outliers: {outlier_cols}",
                'columns': outlier_cols
            })

        # Overall assessment
        if quality_score >= 90:
            overall_quality = 'excellent'
        elif quality_score >= 75:
            overall_quality = 'good'
        elif quality_score >= 60:
            overall_quality = 'fair'
        else:
            overall_quality = 'poor'

        return {
            'overall_quality': overall_quality,
            'quality_score': quality_score,
            'total_issues': len(quality_issues),
            'issues': quality_issues,
            'dataset_summary': {
                'rows': len(df),
                'columns': len(df.columns),
                'missing_values': int(total_missing),
                'duplicate_rows': int(duplicate_rows)
            }
        }

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name"""
        if name == "analyze_dataset":
            return await self._analyze_dataset(
                arguments["path"],
                arguments.get("sample_size", 1000)
            )
        elif name == "calculate_statistics":
            return await self._calculate_statistics(
                arguments["path"],
                arguments.get("columns")
            )
        elif name == "find_correlations":
            return await self._find_correlations(
                arguments["path"],
                arguments.get("method", "pearson"),
                arguments.get("min_correlation", 0.3)
            )
        elif name == "detect_outliers":
            return await self._detect_outliers(
                arguments["path"],
                arguments["column"],
                arguments.get("method", "iqr")
            )
        elif name == "generate_visualization":
            return await self._generate_visualization(
                arguments["path"],
                arguments.get("plot_type", "histogram"),
                arguments.get("x_column"),
                arguments.get("y_column")
            )
        elif name == "assess_data_quality":
            return await self._assess_data_quality(arguments["path"])
        else:
            raise ValueError(f"Unknown tool: {name}")


if __name__ == "__main__":
    # Run as stdio server
    import argparse

    parser = argparse.ArgumentParser(description="Data Science MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run as stdio server")
    args = parser.parse_args()

    if args.stdio:
        server = DataScienceMCPServer()
        asyncio.run(server.start_stdio_server())
    else:
        print("Data Science MCP Server")
        print("Run with --stdio to start the server")