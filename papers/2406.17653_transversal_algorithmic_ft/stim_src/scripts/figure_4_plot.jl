include(joinpath(@__DIR__, "plot_utils.jl"))

using JSON, DataFrames
using HypothesisTests: BinomialTest, confint

function injection_error_rate(p_injected, p, d)
    injection_results = JSON.parsefile(joinpath(@__DIR__, "../results/s_injection/decoder=mle.json"))
    for result in injection_results
        if result["d"] == d && result["noise_spec"]["p"] == p && result["noise_spec"]["p_injected"] == p_injected
            p_input = result["ler"]
            x_nes_input = result["num_les"]
            x_nss_input = result["num_ps"]
            return p_input, x_nes_input, x_nss_input
        end
    end
    @warn "No result found for d = $d, p = $p, p_injected = $p_injected"
    return p_injected, 0, 0
end

function figure_4_one_level_data()
    results = JSON.parsefile(joinpath(@__DIR__, "../results/s_factory/decoder=mle.json"))
    df = DataFrame()
    for result in results
        haskey(result["noise_spec"], "p_injected") || continue
        p_input, x_nes_input, x_nss_input = injection_error_rate(result["noise_spec"]["p_injected"], result["noise_spec"]["p"], result["d"])
        df = [df; DataFrame([Dict(
            "d" => result["d"],
            "p" => result["noise_spec"]["p"],
            "p_injected" => result["noise_spec"]["p_injected"],
            "p_input" => p_input,
            "x_nes_input" => x_nes_input,
            "x_nss_input" => x_nss_input,
            "num_samples" => result["num_samples"],
            "num_ps" => result["num_ps"],
            "num_les" => result["num_les"]
        )])]
    end
    return df
end

function figure_4_one_level(p, show_post_selection_rate::Bool=false)
    df = figure_4_one_level_data()
    ax, fig = generate_fig(; 
        # usetex = true, 
        # legend_font_size = 5,
        figsize=(2.5, 3.5))
    ideal_xs = 10 .^ (-1.6:0.01:-0.4)
    ideal_ys = [s_factory_output_fidelity(x)[show_post_selection_rate ? 2 : 1] for x in ideal_xs]
    ax.plot(ideal_xs, ideal_ys; 
        # label=raw"$y = \frac{7x^3(1-x)^4 + x^7}{7x^3(1-x)^4 + x^7 + (1-x)^7 + 7x^4(1-x)^3}$", 
        label = "Ideal",
        color="black", linestyle=":")
    ds = [3, 5, 7, 9]
    sort!(df, :p_input)
    sort!(df, :p)
    unique_ds = sort(unique(df[!, :d]))
    colors_dict = Dict(
        0.0003 => [shade_color(show_post_selection_rate ? "red" : "blue", -(1 - i/length(ds))) for i = 1:length(ds)],
        0.001 => [shade_color(show_post_selection_rate ? "red" : "orange", -(1 - i/(length(ds)+1))) for i = 1:length(ds)],
        0.003 => [shade_color(show_post_selection_rate ? "red" : "red", -(1 - i/length(ds))) for i = 1:length(ds)],
    )
    marker_shape = show_post_selection_rate ? "d" : "o"
    markers_dict = Dict(
        0.0003 => [marker_shape],
        0.001 => [marker_shape],
        0.003 => [marker_shape]
    )

    total_number_key = show_post_selection_rate ? :num_samples : :num_ps
    true_number_key = show_post_selection_rate ? :num_ps : :num_les
    x_nss_lines = Vector{Float64}[]
    x_nes_lines = Vector{Float64}[]
    y_nes_lines = Vector{Int}[]
    y_nss_lines = Vector{Int}[]
    for d in unique_ds
        df_line = filter(row -> row[:d] == d && row[:p] == p, df)
        x_nes_line = df_line[!, :x_nes_input]
        x_nss_line = df_line[!, :x_nss_input]
        nes_line = df_line[!, true_number_key]
        nss_line = df_line[!, total_number_key]
        push!(x_nes_lines, x_nes_line)
        push!(x_nss_lines, x_nss_line)
        push!(y_nes_lines, nes_line)
        push!(y_nss_lines, nss_line)
    end
    lines = [ResultLine(x_nes, x_nss, y_nes, y_nss) for (x_nes, x_nss, y_nes, y_nss) in zip(x_nes_lines, x_nss_lines, y_nes_lines, y_nss_lines)]
    ylabel = show_post_selection_rate ? "Post-selection rate" : "Output infidelity"
    plot_ler_with_error_bar!(ax, lines, ["d = $d" for d in unique_ds]; 
        colors = colors_dict[p],
        markers = markers_dict[p],
        markersize = 4.0,
        markerfacecolors = [shade_color(color, -0.2) for color in colors_dict[p]],
        markeredgecolors = [shade_color(color, 0.2) for color in colors_dict[p]],
        xlabel="Input infidelity", ylabel=ylabel, 
        # ylim_min = 10^-4, ylim_max = 0.9,
        xscale = "log",
        subplot_left = 0.25, subplot_right = 0.95, 
        subplot_bottom = 0.15, subplot_top = 0.95,

        legend_loc = show_post_selection_rate ? "lower left" : "lower right",
        bbox_to_anchor = nothing,
    )

    filename = show_post_selection_rate ? "fig_4_one_level_post_selection_rate_$(p).pdf" : "fig_4_one_level_$(p).pdf"
    plt.savefig(joinpath(@__DIR__, "../figs", filename))
    return fig
end

figure_4_one_level(0.001, true)
figure_4_one_level(0.001, false)

function figure_4_two_level_data()
    p_injected = 0.1
    p = 0.001
    d1, d2, d3 = 3, 5, 9
    results_0 = JSON.parsefile(joinpath(@__DIR__, "../results/s_injection/decoder=mle.json"))
    result_0 = filter(x -> x["d"] == d2 && x["noise_spec"]["p"] == p && x["noise_spec"]["p_injected"] == p_injected, results_0)[]
    p_input = result_0["ler"]
    df_0 = DataFrame(
        Dict(
            "d1" => d1,
            "d2" => d2,
            "d3" => d3,
            "p" => p,
            "p_injected" => p_injected,
            "p_input" => p_input,
            "num_samples" => result_0["num_samples"],
            "num_ps" => result_0["num_ps"],
            "num_les" => result_0["num_les"],
            "round" => 0
        )
    )
    # @show df_0
    
    results_1 = JSON.parsefile(joinpath(@__DIR__, "../results/s_factory/decoder=mle.json"))
    result_1 = filter(x -> x["d"] == d2 && x["noise_spec"]["p"] == p && x["noise_spec"]["p_injected"] == p_injected, results_1)[]
    df_1 = DataFrame(
        Dict(
            "d1" => d1,
            "d2" => d2,
            "d3" => d3,
            "p" => result_1["noise_spec"]["p"],
            "p_injected" => p_injected,
            "p_input" => p_input,
            "num_samples" => result_1["num_samples"],
            "num_ps" => result_1["num_ps"],
            "num_les" => result_1["num_les"],
            "round" => 1
        )
    )
    # @show df_1

    results_2 = JSON.parsefile(joinpath(@__DIR__, "../results/two_level_s_factory/decoder=mle.json"))
    result_2 = results_2[]
    df_2 = DataFrame(
        Dict(
            "d1" => d1,
            "d2" => d2,
            "d3" => result_2["d"],
            "p" => result_2["noise_spec"]["p"],
            "p_injected" => p_injected,
            "p_input" => p_input,
            "num_samples" => result_2["num_samples"],
            "num_ps" => result_2["num_ps"],
            "num_les" => result_2["num_les"],
            "round" => 2
        )
    )
    # @show df_2
    df = [df_0; df_1; df_2]
    # @show df
    return df
end

function figure_4_two_level()
    df = figure_4_two_level_data()
    @show df[1, :]
    ax, fig = generate_fig(; figsize=(2.5, 3.5))
    total_rounds = 2
    y_ideal_lower, y_ideal_upper = confint(BinomialTest(df[1, :num_les], df[1, :num_ps]))
    y_ideal_upper = [y_ideal_upper]
    y_ideal_lower = [y_ideal_lower]
    y_ideal = [df[1, :p_input]]
    for _ = 1:total_rounds
        push!(y_ideal_upper, s_factory_output_fidelity(y_ideal_upper[end])[1])
        push!(y_ideal_lower, s_factory_output_fidelity(y_ideal_lower[end])[1])
        push!(y_ideal, s_factory_output_fidelity(y_ideal[end])[1])
    end
    yerrs = [(y_ideal_upper - y_ideal)'; (y_ideal - y_ideal_lower)']
    @show yerrs
    # line = ResultLine([0, 1, 2], y_ideal; yerrs)
    # plot_line_with_error_bar!(ax, line; 
    #     label="Ideal", 
    #     color="black",
    #     markerfacecolor="white",)
    # ax.plot([i for i = 0:total_rounds], y_ideal_upper; label="Ideal (upper)", color="black", linestyle=":")
    # ax.plot([i for i = 0:total_rounds], y_ideal_lower; label="Ideal (lower)", color="black", linestyle="--")
    ax.plot([i for i = 0:total_rounds], y_ideal; label="Ideal", color="black", linestyle=":")
    
    sort!(df, :round)
    unique_ds = sort(unique(df[!, :d3]))
    xs_lines = Vector{Float64}[]
    nes_lines = Vector{Int}[]
    nss_lines = Vector{Int}[]
    for x in unique_ds
        df_line = filter(row -> row[:d3] == x, df)
        xs_line = df_line[!, :round]
        nes_line = df_line[!, :num_les]
        nss_line = df_line[!, :num_ps]
        push!(xs_lines, xs_line)
        push!(nes_lines, nes_line)
        push!(nss_lines, nss_line)
    end
    xs_lines = [[xs_lines[1][i]] for i = 1:3]
    nes_lines = [[nes_lines[1][i]] for i = 1:3]
    nss_lines = [[nss_lines[1][i]] for i = 1:3]
    lines = [ResultLine(xs_line, nes_line, nss_line) for (xs_line, nes_line, nss_line) in zip(xs_lines, nes_lines, nss_lines)]
    plot_ler_with_error_bar!(ax, lines, ["Simulation", "", ""]; 
        colors = ["orange", ],
        markers = ["o"],
        markerfacecolors = [shade_color("orange", -0.2)],
        markeredgecolors = [shade_color("orange", 0.2)],
        markersize = 4.0,
        alphas = [1.0],
        xlabel="Round of distillation", ylabel="Output infidelity", 
        # ylim_min = 0,
        xscale = "linear",
        yscale = "log",
        xticks = [0, 1, 2],
        legend_loc = "lower left",

        subplot_left = 0.25, subplot_right = 0.95, 
        subplot_bottom = 0.15, subplot_top = 0.95,
    )
    plt.savefig(joinpath(@__DIR__, "../figs", "fig_4_two_level.pdf"))
    return fig
end

figure_4_two_level()
