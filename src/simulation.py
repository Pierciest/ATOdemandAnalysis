import numpy as np
import pandas as pd

def lhs(n, samples):
    result = np.zeros((samples, n))
    for i in range(n):
        result[:, i] = np.random.permutation(np.linspace(0, 1, samples))
    return result

def generate_price_sets(price_min, price_max, num_samples):
    num_products = len(price_min)
    samples = lhs(num_products, samples=num_samples)
    price_sets = samples * (np.array(price_max) - np.array(price_min)) + np.array(price_min)
    return price_sets

def independent_price_demand(prices, base_demand_range=(300, 600), sensitivity_range=(1, 5), noise_std_range=(1, 3), min_demand_threshold=10):
    """
    Generate demand for products based on prices.

    Parameters:
        prices (array-like): Prices of the products.
        base_demand_range (tuple): Range for base demand (min, max).
        sensitivity_range (tuple): Range for sensitivity to price (min, max).
        noise_std_range (tuple): Range for noise standard deviation (min, max).
        min_demand_threshold (float): Minimum demand to prevent excessive zeros.

    Returns:
        np.ndarray: Non-negative demands for each product.
    """
    n_products = len(prices)

    # Generate base demand, sensitivity, and noise levels
    base_demand = np.random.uniform(*base_demand_range, size=n_products)
    sensitivity = np.random.uniform(*sensitivity_range, size=n_products)
    noise_std = np.random.uniform(*noise_std_range, size=n_products)

    # Generate random noise
    noise = np.random.normal(0, noise_std, size=n_products)

    # Calculate demand
    demand = base_demand - sensitivity * prices + noise

    # Apply minimum threshold for demand
    demand = np.maximum(demand, min_demand_threshold)
    return demand


def generate_scenarios(prices, n_scenarios):
    scenario_demands = [independent_price_demand(prices) for _ in range(n_scenarios)]
    return np.array(scenario_demands)

def compute_revenues_from_cut(scenario_demands_matrix, price_sets, manufacturing_costs, start_index):
    n_price_sets = price_sets.shape[0]
    adjusted_revenues = np.zeros(n_price_sets)
    for i in range(n_price_sets):
        remaining_demands = scenario_demands_matrix[i, start_index:]
        avg_demand = np.mean(remaining_demands, axis=0)
        product_revenues = (avg_demand * price_sets[i]) - manufacturing_costs
        adjusted_revenues[i] = np.sum(product_revenues)
    return adjusted_revenues

def create_revenue_dataframe(price_sets, adjusted_revenues):
    column_names = [f'P{i+1}' for i in range(price_sets.shape[1])]
    df = pd.DataFrame(price_sets, columns=column_names)
    df['Revenue'] = adjusted_revenues
    return df

import pandas as pd
import numpy as np

def run_simulation(price_min, price_max, manufacturing_costs, num_price_samples, scenario_steps, cut_n):
    """
    Simulates the ATO demand and revenue based on price sets and scenarios.

    Returns:
        avg_revenues_df (DataFrame): Average revenue for each price set after cut.
        demand_df (DataFrame): Demand values for each price set and scenario.
        scenario_revenues_df (DataFrame): Revenue values for each price set and scenario.
        uncut_revenues_df (DataFrame): Revenue values for each price set and scenario before cut.
    """
    # Generate random price sets
    price_sets = np.random.uniform(price_min, price_max, size=(num_price_samples, len(price_min)))

    # Create a DataFrame for price sets
    price_set_df = pd.DataFrame(price_sets, columns=[f'P{i+1}' for i in range(len(price_min))])
    price_set_df['PriceSet'] = price_set_df.index

    # Generate demand and revenue data
    demand_data = []
    scenario_revenues = []
    uncut_revenues = []

    for i, price_set in enumerate(price_sets):
        for scenario in range(scenario_steps):
            # Simulate demands using the independent_price_demand function
            demands = independent_price_demand(price_set)
            revenue = np.sum(demands * price_set) - np.sum(manufacturing_costs)

            # Append data
            demand_data.append({"PriceSet": i, "Scenario": scenario, "Demands": demands.tolist()})
            scenario_revenues.append({"PriceSet": i, "Scenario": scenario, "Revenue": revenue})

            if scenario >= cut_n:
                uncut_revenues.append({"PriceSet": i, "Scenario": scenario, "Revenue": revenue})

    # Create DataFrames
    demand_df = pd.DataFrame(demand_data)
    scenario_revenues_df = pd.DataFrame(scenario_revenues)
    uncut_revenues_df = pd.DataFrame(uncut_revenues)

    # Compute average revenue after cut
    avg_revenues_df = (
        scenario_revenues_df[scenario_revenues_df["Scenario"] >= cut_n]
        .groupby("PriceSet")["Revenue"]
        .mean()
        .reset_index()
    )

    # Merge price set details into avg_revenues_df
    avg_revenues_df = avg_revenues_df.merge(price_set_df, on="PriceSet", how="left")

    return avg_revenues_df, demand_df, scenario_revenues_df, uncut_revenues_df


